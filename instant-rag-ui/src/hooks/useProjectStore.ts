import { create } from 'zustand';
import { createProject, fetchProjects, deleteProject } from '@/services/api';

export interface Project {
  id: string;
  name: string;
  createdAt: Date;
}

interface ProjectState {
  projects: Project[];
  selectedProjectId: string | null;
  isLoading: boolean;
  addProject: (name: string) => Promise<void>;
  removeProject: (id: string) => Promise<void>;
  selectProject: (id: string | null) => void;
  loadProjects: () => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  selectedProjectId: null,
  isLoading: false,
  
  addProject: async (name) => {
    set({ isLoading: true });
    try {
      const newProject = await createProject(name);
      
      if (newProject) {
        set((state) => ({
          projects: [...state.projects, newProject],
          selectedProjectId: newProject.id,
          isLoading: false,
        }));
      } else {
        // Fallback to local creation if API call fails
        console.warn('API call failed, creating project locally');
        set((state) => {
          const localProject = {
            id: Date.now().toString(),
            name,
            createdAt: new Date(),
          };
          
          return {
            projects: [...state.projects, localProject],
            selectedProjectId: localProject.id,
            isLoading: false,
          };
        });
      }
    } catch (error) {
      console.error('Error creating project:', error);
      set({ isLoading: false });
    }
  },
  
  removeProject: async (id) => {
    set({ isLoading: true });
    try {
      const success = await deleteProject(id);
      
      if (success) {
        set((state) => {
          const filteredProjects = state.projects.filter(project => project.id !== id);
          const newSelectedId = state.selectedProjectId === id
            ? (filteredProjects.length > 0 ? filteredProjects[0].id : null)
            : state.selectedProjectId;
            
          return {
            projects: filteredProjects,
            selectedProjectId: newSelectedId,
            isLoading: false,
          };
        });
      } else {
        console.error('Failed to delete project from backend');
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('Error removing project:', error);
      set({ isLoading: false });
    }
  },
  
  selectProject: (id) => set({
    selectedProjectId: id,
  }),
  
  loadProjects: async () => {
    set({ isLoading: true });
    try {
      const projects = await fetchProjects();
      set({ projects, isLoading: false });
      
      // Select the first project if none is selected and projects exist
      const { selectedProjectId } = get();
      if (!selectedProjectId && projects.length > 0) {
        set({ selectedProjectId: projects[0].id });
      }
    } catch (error) {
      console.error('Error loading projects:', error);
      
      // Set loading to false for all errors
      set({ isLoading: false });
      
      // We don't need to handle 401 errors here specifically anymore
      // The error will be caught by the global error handlers in AppLayout and SidebarProjects
      // which will redirect to login
    }
  },
}));
