# Test Document for Instant-RAG

This is a sample markdown document to test the file upload functionality in Instant-RAG.

## Features

- PDF, Markdown, and image file support
- Drag and drop interface
- Progress tracking during upload
- File validation

## Sample Code

```javascript
function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  return fetch('/api/upload', {
    method: 'POST',
    body: formData
  }).then(response => response.json());
}
```

## Sample Table

| File Type | Extension | Max Size |
|-----------|-----------|----------|
| PDF       | .pdf      | 10MB     |
| Markdown  | .md       | 10MB     |
| PNG Image | .png      | 10MB     |
| JPEG Image| .jpg, .jpeg| 10MB    |

## Conclusion

This document is used to test the file upload functionality in the Instant-RAG application.
