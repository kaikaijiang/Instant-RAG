"use client";

import { useEffect } from "react";
import SidebarProjects from "@/components/SidebarProjects";
import ProjectWorkspace from "@/components/ProjectWorkspace";
import { useProjectStore } from "@/hooks/useProjectStore";
import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { toast } from "@/hooks/use-toast";

export default function AppLayout() {
  const { selectedProjectId, loadProjects } = useProjectStore();
  const { data: session } = useSession();
  const router = useRouter();

  // Refresh the session periodically to keep the token valid
  useEffect(() => {
    // Check session every 5 minutes
    const interval = setInterval(() => {
      // This will trigger a session refresh if needed
      const checkSession = async () => {
        try {
          // This will refresh the session if it's still valid but close to expiring
          await fetch('/api/auth/session');
          console.log('Session refreshed');
        } catch (error) {
          console.error('Error refreshing session:', error);
        }
      };
      
      checkSession();
    }, 5 * 60 * 1000); // 5 minutes
    
    return () => clearInterval(interval);
  }, []);

  // Handle authentication errors
  useEffect(() => {
    const handleAuthError = (event: ErrorEvent) => {
      // Check if the error is related to authentication
      if (event.error?.message?.includes('401') || 
          event.message?.includes('401') ||
          event.error?.toString().includes('Authentication failed')) {
        console.error('Authentication error detected in error event:', event);
        toast({
          variant: "destructive",
          title: "Authentication Error",
          description: "Your session has expired. Please log in again."
        });
        // Redirect to login page - force a redirect
        console.log("Redirecting to login page due to authentication error in error event");
        signOut({ callbackUrl: "/login", redirect: true });
      }
    };

    // Add global error event listener
    window.addEventListener('error', handleAuthError);
    
    // Handle unhandled promise rejections
    const handlePromiseRejection = (event: PromiseRejectionEvent) => {
      if (event.reason?.message?.includes('401') || 
          event.reason?.toString().includes('Authentication failed')) {
        console.error('Authentication error in promise rejection:', event.reason);
        toast({
          variant: "destructive",
          title: "Authentication Error",
          description: "Your session has expired. Please log in again."
        });
        console.log("Redirecting to login page due to authentication error in promise rejection");
        signOut({ callbackUrl: "/login", redirect: true });
      }
    };
    
    window.addEventListener('unhandledrejection', handlePromiseRejection);

    return () => {
      window.removeEventListener('error', handleAuthError);
      window.removeEventListener('unhandledrejection', handlePromiseRejection);
    };
  }, []);

  const handleLogout = () => {
    signOut({ callbackUrl: "/login" });
  };

  return (
    <>
      <div className="flex h-screen bg-background">
        <SidebarProjects />
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex justify-end p-2 border-b">
            {session?.user?.email && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {session.user.email}
                </span>
                <Button variant="outline" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </div>
            )}
          </div>
          <div className="flex-1 overflow-auto">
            <ProjectWorkspace projectId={selectedProjectId} />
          </div>
        </div>
      </div>
    </>
  );
}
