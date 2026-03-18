"use client";

import { useSessionMigration } from '../hooks/useSessionMigration';

/**
 * Component that automatically migrates session data when user signs in.
 * Must be a client component to use hooks.
 */
export default function SessionMigrationWrapper() {
  useSessionMigration();
  return null; // This component doesn't render anything
}
