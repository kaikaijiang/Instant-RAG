# Instant-RAG

An AI-powered multi-project RAG (Retrieval-Augmented Generation) system.

![Document upload](https://github.com/kaikaijiang/Instant-RAG/blob/main/instant-rag-ui/web_example.png)
![Chat with document](https://github.com/kaikaijiang/Instant-RAG/blob/main/instant-rag-ui/web_example_chat.png)

## Features

- Create and manage multiple RAG projects
- Upload and process documents (PDF, TXT, DOCX)
- Chat with AI using your documents as context
- Dark mode UI with clean, modern design

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **UI**: TailwindCSS + shadcn/ui components
- **State Management**: Zustand
- **File Uploads**: react-dropzone
- **Notifications**: react-hot-toast

## Project Structure

```
instant-rag/
├── src/
│   ├── app/                 # Next.js App Router
│   ├── components/          # React components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── SidebarProjects.tsx
│   │   ├── ProjectWorkspace.tsx
│   │   └── AppLayout.tsx
│   ├── hooks/               # Custom React hooks
│   │   ├── useProjectStore.ts
│   │   └── useFileUpload.ts
│   ├── services/            # API services
│   │   └── api.ts
│   └── utils/               # Utility functions
│       └── helpers.ts
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Create a Project**: Click the "+" button in the sidebar to create a new project.
2. **Upload Documents**: Select a project, then use the drag-and-drop area to upload documents.
3. **Chat with AI**: Once documents are uploaded, use the chat interface to ask questions about your documents.

## Development

- **Add new shadcn/ui components**:
  ```bash
  npx shadcn@latest add [component-name]
  ```

- **Build for production**:
  ```bash
  npm run build
  ```

## License

MIT
