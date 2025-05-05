"use client";

import { useState, useRef, useEffect } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useProjectStore } from "@/hooks/useProjectStore";
import { toast } from "@/hooks/use-toast";
import { signOut } from "next-auth/react";

export default function SidebarProjects() {
  const { 
    projects, 
    selectedProjectId, 
    addProject, 
    removeProject, 
    selectProject,
    loadProjects,
    isLoading 
  } = useProjectStore();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [contextMenuVisible, setContextMenuVisible] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [contextMenuProjectId, setContextMenuProjectId] = useState<string | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null);
  const contextMenuRef = useRef<HTMLDivElement>(null);

  // Load projects when component mounts and refresh periodically
  useEffect(() => {
    const loadProjectsWithErrorHandling = async () => {
      try {
        await loadProjects();
      } catch (error) {
        console.error('Error loading projects in SidebarProjects:', error);
        
        // Check if it's an authentication error
        if (error instanceof Error && 
            (error.message.includes('401') || 
             error.message.includes('Authentication failed'))) {
          toast({
            variant: "destructive",
            title: "Authentication Error",
            description: "Your session has expired. Please log in again."
          });
          // Redirect to login page - force a redirect
          console.log("Redirecting to login page due to authentication error");
          signOut({ callbackUrl: "/login", redirect: true });
        }
      }
    };
    
    // Load projects immediately when component mounts
    loadProjectsWithErrorHandling();
    
    // Then refresh projects every 30 seconds
    const interval = setInterval(() => {
      loadProjectsWithErrorHandling();
    }, 30 * 1000); // 30 seconds
    
    return () => clearInterval(interval);
  }, [loadProjects]);

  const handleCreateProject = () => {
    if (newProjectName.trim()) {
      addProject(newProjectName.trim());
      setNewProjectName("");
      setIsDialogOpen(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleCreateProject();
    }
  };

  const handleContextMenu = (e: React.MouseEvent, projectId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenuVisible(true);
    setContextMenuPosition({ x: e.clientX, y: e.clientY });
    setContextMenuProjectId(projectId);
  };

  const handleDeleteProject = () => {
    if (projectToDelete) {
      removeProject(projectToDelete).catch(error => {
        console.error('Failed to delete project:', error);
        // Could add a toast notification here
      });
      setDeleteConfirmOpen(false);
      setProjectToDelete(null);
    }
  };

  // Close context menu when clicking outside
  const handleClickOutside = (e: MouseEvent) => {
    if (contextMenuRef.current && !contextMenuRef.current.contains(e.target as Node)) {
      setContextMenuVisible(false);
    }
  };

  // Add event listener for clicks outside context menu
  useEffect(() => {
    if (contextMenuVisible) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [contextMenuVisible]);

  return (
    <div className="h-full w-64 bg-background border-r border-border p-4 flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Projects</h2>
      </div>
      
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="text-muted-foreground text-center py-8">
            Loading projects...
          </div>
        ) : projects.length === 0 ? (
          <div className="text-muted-foreground text-center py-8">
            No projects yet. Create your first project to get started.
          </div>
        ) : (
          <ul className="space-y-2">
            {projects.map((project) => (
              <li 
                key={project.id}
                className={`flex items-center justify-between p-2 rounded-md cursor-pointer ${
                  selectedProjectId === project.id 
                    ? "bg-accent text-accent-foreground" 
                    : "hover:bg-muted"
                }`}
                onClick={() => selectProject(project.id)}
                onContextMenu={(e) => handleContextMenu(e, project.id)}
              >
                <span className="truncate">{project.name}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation();
                    setProjectToDelete(project.id);
                    setDeleteConfirmOpen(true);
                  }}
                  disabled={isLoading}
                  aria-label={`Delete ${project.name}`}
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* New Project Button at the bottom */}
      <div className="mt-4 pt-4 border-t border-border">
        <Button 
          variant="outline" 
          className="w-full flex items-center justify-center gap-2"
          onClick={() => setIsDialogOpen(true)}
          aria-label="Create new project"
        >
          <Plus className="h-4 w-4" />
          <span>New Project</span>
        </Button>
      </div>

      {/* New Project Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Enter a name for your new project.
            </DialogDescription>
          </DialogHeader>
          <Input
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            placeholder="Project name"
            className="mt-2"
            autoFocus
            onKeyDown={handleKeyDown}
          />
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isLoading}>
              Cancel
            </Button>
            <Button onClick={handleCreateProject} disabled={isLoading}>
              {isLoading ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this project? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <Button 
              variant="outline" 
              onClick={() => setDeleteConfirmOpen(false)} 
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteProject} 
              disabled={isLoading}
            >
              {isLoading ? "Deleting..." : "Yes, Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Context Menu */}
      {contextMenuVisible && contextMenuProjectId && (
        <div
          ref={contextMenuRef}
          className="absolute bg-background border border-border rounded-md shadow-md py-1 z-50"
          style={{
            top: `${contextMenuPosition.y}px`,
            left: `${contextMenuPosition.x}px`,
          }}
        >
          <button
            className="w-full text-left px-4 py-2 hover:bg-muted text-sm"
            onClick={() => {
              if (contextMenuProjectId) {
                setProjectToDelete(contextMenuProjectId);
                setDeleteConfirmOpen(true);
                setContextMenuVisible(false);
              }
            }}
            disabled={isLoading}
          >
            Delete Project
          </button>
        </div>
      )}
    </div>
  );
}
