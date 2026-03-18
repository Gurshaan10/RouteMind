"""
Script to generate and store vector embeddings for all activities.

Run once after setting up pgvector:
    cd backend
    python scripts/generate_embeddings.py

After running, set RAG_ENABLED=true in your .env file.
"""
import asyncio
import sys
import os
import logging

# Ensure the backend app is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.db.models import Activity, ActivityEmbedding
from app.services.embedding_service import build_activity_embedding_text, generate_embedding
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 20  # Activities per batch (to respect OpenAI rate limits)


async def generate_all_embeddings():
    """Generate embeddings for all activities and store them."""
    db = SessionLocal()
    try:
        # Check pgvector is available
        try:
            db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
            logger.info("pgvector extension confirmed available")
        except Exception:
            logger.error("pgvector extension not found. Run: CREATE EXTENSION vector;")
            return

        # Get all activities
        activities = db.query(Activity).all()
        total = len(activities)
        logger.info(f"Found {total} activities to embed")

        if total == 0:
            logger.warning("No activities found in database")
            return

        # Get already-embedded activity IDs
        existing_ids = {
            row[0] for row in db.query(ActivityEmbedding.activity_id).all()
        }
        to_embed = [a for a in activities if a.id not in existing_ids]
        logger.info(f"{len(existing_ids)} already embedded, {len(to_embed)} remaining")

        if not to_embed:
            logger.info("All activities already have embeddings. Done.")
            return

        # Process in batches
        success_count = 0
        error_count = 0

        for i in range(0, len(to_embed), BATCH_SIZE):
            batch = to_embed[i:i + BATCH_SIZE]
            logger.info(f"Processing batch {i // BATCH_SIZE + 1} ({len(batch)} activities)...")

            for activity in batch:
                try:
                    text_repr = build_activity_embedding_text(activity)
                    embedding = await generate_embedding(text_repr)

                    # Store as vector string for pgvector
                    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

                    # Insert or update using raw SQL to leverage pgvector type casting
                    db.execute(text("""
                        INSERT INTO activity_embeddings (activity_id, embedding_vec, created_at)
                        VALUES (:activity_id, CAST(:embedding AS vector), NOW())
                        ON CONFLICT (activity_id) DO UPDATE
                        SET embedding_vec = CAST(:embedding AS vector), created_at = NOW()
                    """), {"activity_id": activity.id, "embedding": embedding_str})

                    success_count += 1
                    if success_count % 50 == 0:
                        db.commit()
                        logger.info(f"  Committed {success_count}/{len(to_embed)} embeddings")

                except Exception as e:
                    logger.error(f"  Failed to embed activity {activity.id} ({activity.name}): {e}")
                    error_count += 1

            # Small delay between batches to respect rate limits
            await asyncio.sleep(0.5)

        db.commit()
        logger.info(
            f"\nDone! Successfully embedded {success_count} activities. "
            f"Errors: {error_count}."
        )
        logger.info("\nNext step: Set RAG_ENABLED=true in your .env file to activate semantic retrieval.")

    finally:
        db.close()


if __name__ == "__main__":
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set in .env file")
        sys.exit(1)

    asyncio.run(generate_all_embeddings())
