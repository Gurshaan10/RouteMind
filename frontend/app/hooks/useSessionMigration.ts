import { useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { api } from '../lib/api';

/**
 * Hook to automatically migrate session data when user signs in.
 * This will move any itineraries created before login to the user's account.
 */
export function useSessionMigration() {
  const { data: session, status } = useSession();
  const hasMigrated = useRef(false);

  useEffect(() => {
    // Only run once when user becomes authenticated
    if (status === 'authenticated' && session && !hasMigrated.current) {
      const migrateData = async () => {
        try {
          const authToken = (session as any)?.accessToken;
          if (!authToken) return;

          const result = await api.migrateSession(authToken);

          if (result.migrated_count > 0) {
            console.log(`✅ Migrated ${result.migrated_count} itineraries to your account`);
          }

          hasMigrated.current = true;
        } catch (error) {
          console.error('Failed to migrate session data:', error);
        }
      };

      migrateData();
    }
  }, [session, status]);
}
