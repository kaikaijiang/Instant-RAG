import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useChatStore, ChatMessage } from "@/hooks/useChatStore";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

interface ChatProps {
  projectId: string;
}

export default function Chat({ projectId }: ChatProps) {
  const { messages, isLoading, sendMessage, addMessage } = useChatStore();
  const [inputValue, setInputValue] = useState("");
  const [topK, setTopK] = useState(10);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    await sendMessage(inputValue, topK);
    setInputValue("");
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground text-center">
              Ask a question about your documents to get started.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))
        )}
        {isLoading && (
          <div className="flex justify-center py-2">
            <Spinner size="md" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="border-t p-2">
        <div className="flex items-center gap-2 mb-2">
          <Label htmlFor="topk" className="whitespace-nowrap ml-auto">Top K:</Label>
          <Input
            id="topk"
            type="number"
            min="1"
            max="20"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value) || 10)}
            className="w-20"
          />
          <span className="text-xs text-muted-foreground">Number of chunks to retrieve</span>
        </div>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !inputValue.trim()}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}

interface ChatBubbleProps {
  message: ChatMessage;
}

function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";
  
  return (
    <div
      className={cn(
        "flex",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        )}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
        
        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 text-xs border-t pt-1 opacity-80">
            <p className="font-medium">Sources:</p>
            <ul className="list-disc list-inside">
              {message.citations.map((citation, index) => (
                <li key={index}>
                  {citation.documentName}
                  {citation.pageNumber && ` (p. ${citation.pageNumber})`}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Document References */}
        {message.references && message.references.length > 0 && (
          <div className="mt-2 text-xs border-t pt-1 opacity-80">
            <p className="font-medium">References:</p>
            <ul className="list-disc list-inside">
              {message.references.map((reference, index) => (
                <li key={index}>
                  {reference.startsWith('http') || reference.startsWith('https') ? (
                    <a 
                      href={reference} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {reference}
                    </a>
                  ) : (
                    reference
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Images */}
        {message.images && message.images.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.images.map((image, index) => (
              <ImageThumbnail 
                key={index} 
                image={image} 
                index={index} 
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface ImageThumbnailProps {
  image: string;
  index: number;
}

function ImageThumbnail({ image, index }: ImageThumbnailProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1); // Initial zoom level is 1 (100%)
  const [position, setPosition] = useState({ x: 0, y: 0 }); // Track image position for dragging
  const [isDragging, setIsDragging] = useState(false); // Track if currently dragging
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 }); // Starting point of drag
  const [velocity, setVelocity] = useState({ x: 0, y: 0 }); // Track velocity for inertia
  const [lastPosition, setLastPosition] = useState({ x: 0, y: 0 }); // Last position for velocity calculation
  const [lastMoveTime, setLastMoveTime] = useState(0); // Last move time for velocity calculation
  const containerRef = useRef<HTMLDivElement>(null); // Reference to the container
  
  // Simple placeholder SVG for errors
  const placeholderImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iMTIiIHk9IjEyIiBmb250LXNpemU9IjEyIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBhbGlnbm1lbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iIzk5OTk5OSI+P1w8L3RleHQ+PC9zdmc+';
  
  // Function to zoom in (increase zoom level)
  const zoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.25, 3)); // Max zoom: 300%
  };
  
  // Function to zoom out (decrease zoom level)
  const zoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.25, 0.5)); // Min zoom: 50%
  };
  
  // Function to reset zoom level
  const resetZoom = () => {
    setZoomLevel(1);
  };
  
  // Reset zoom level and position when dialog is closed
  useEffect(() => {
    if (!isOpen) {
      setZoomLevel(1);
      setPosition({ x: 0, y: 0 });
    }
  }, [isOpen]);
  
  // Handle start of drag operation
  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoomLevel > 1) { // Only enable dragging when zoomed in
      setIsDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
      setLastPosition({ x: position.x, y: position.y });
      setLastMoveTime(Date.now());
      setVelocity({ x: 0, y: 0 });
      
      // Prevent default behavior to avoid text selection during drag
      e.preventDefault();
    }
  };
  
  // Handle drag movement
  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      const now = Date.now();
      const newPosition = {
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      };
      
      // Calculate velocity (pixels per millisecond)
      if (now - lastMoveTime > 0) {
        setVelocity({
          x: (newPosition.x - lastPosition.x) / (now - lastMoveTime) * 15, // Scale factor for more noticeable effect
          y: (newPosition.y - lastPosition.y) / (now - lastMoveTime) * 15
        });
      }
      
      setPosition(newPosition);
      setLastPosition(newPosition);
      setLastMoveTime(now);
    }
  };
  
  // Handle end of drag operation (drop)
  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      
      // Apply inertia effect if velocity is significant
      if (Math.abs(velocity.x) > 0.01 || Math.abs(velocity.y) > 0.01) {
        applyInertia();
      } else {
        // If dropped near boundary, snap to it
        snapToBoundaries();
      }
    }
  };
  
  // Apply inertia effect after dropping
  const applyInertia = () => {
    let currentVelocity = { ...velocity };
    let currentPosition = { ...position };
    let animationFrameId: number;
    
    const animate = () => {
      // Apply friction to gradually reduce velocity
      currentVelocity = {
        x: currentVelocity.x * 0.95,
        y: currentVelocity.y * 0.95
      };
      
      // Update position based on velocity
      currentPosition = {
        x: currentPosition.x + currentVelocity.x,
        y: currentPosition.y + currentVelocity.y
      };
      
      // Apply position constraints
      const constraints = getPositionConstraints(currentPosition);
      currentPosition = constraints.position;
      
      // If velocity is very low or we hit a boundary, stop animation
      if ((Math.abs(currentVelocity.x) < 0.1 && Math.abs(currentVelocity.y) < 0.1) || 
          constraints.hitBoundary) {
        setPosition(currentPosition);
        cancelAnimationFrame(animationFrameId);
        return;
      }
      
      setPosition(currentPosition);
      animationFrameId = requestAnimationFrame(animate);
    };
    
    animationFrameId = requestAnimationFrame(animate);
    
    // Cleanup function to cancel animation if component unmounts
    return () => cancelAnimationFrame(animationFrameId);
  };
  
  // Snap to boundaries if image is dropped near edge
  const snapToBoundaries = () => {
    const constraints = getPositionConstraints(position);
    if (constraints.position.x !== position.x || constraints.position.y !== position.y) {
      // Animate the snap
      const startPosition = { ...position };
      const endPosition = constraints.position;
      const startTime = Date.now();
      const duration = 300; // ms
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic function for smooth deceleration
        const easeOut = 1 - Math.pow(1 - progress, 3);
        
        const newPosition = {
          x: startPosition.x + (endPosition.x - startPosition.x) * easeOut,
          y: startPosition.y + (endPosition.y - startPosition.y) * easeOut
        };
        
        setPosition(newPosition);
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      
      requestAnimationFrame(animate);
    }
  };
  
  // Get position constraints based on container and image size
  const getPositionConstraints = (pos: { x: number, y: number }) => {
    if (!containerRef.current) {
      return { position: pos, hitBoundary: false };
    }
    
    const container = containerRef.current;
    const containerRect = container.getBoundingClientRect();
    
    // Estimate image dimensions based on zoom level
    // This is an approximation since we don't have direct access to the image dimensions
    const imageWidth = containerRect.width * zoomLevel;
    const imageHeight = containerRect.height * zoomLevel;
    
    // Calculate the maximum allowed position values
    const maxX = (imageWidth - containerRect.width) / 2;
    const maxY = (imageHeight - containerRect.height) / 2;
    
    // Constrain position within boundaries
    const constrainedPosition = {
      x: Math.max(-maxX, Math.min(maxX, pos.x)),
      y: Math.max(-maxY, Math.min(maxY, pos.y))
    };
    
    // Check if we hit a boundary
    const hitBoundary = 
      constrainedPosition.x !== pos.x || 
      constrainedPosition.y !== pos.y;
    
    return { position: constrainedPosition, hitBoundary };
  };
  
  // Add event listeners for drag operations that might happen outside the image
  useEffect(() => {
    if (isOpen) {
      const handleGlobalMouseUp = () => {
        setIsDragging(false);
      };
      
      const handleGlobalMouseMove = (e: MouseEvent) => {
        if (isDragging) {
          setPosition({
            x: e.clientX - dragStart.x,
            y: e.clientY - dragStart.y
          });
        }
      };
      
      window.addEventListener('mouseup', handleGlobalMouseUp);
      window.addEventListener('mousemove', handleGlobalMouseMove);
      
      return () => {
        window.removeEventListener('mouseup', handleGlobalMouseUp);
        window.removeEventListener('mousemove', handleGlobalMouseMove);
      };
    }
  }, [isOpen, isDragging, dragStart]);
  
  // If image is undefined or empty, show a placeholder
  if (!image) {
    return (
      <div className="w-24 h-24 bg-gray-200 rounded-md flex items-center justify-center text-xs text-gray-500">
        No image data
      </div>
    );
  }
  
  return (
    <>
      <div className="relative">
        <img
          src={imageError ? placeholderImage : image}
          alt={`Generated image ${index + 1}`}
          className="w-24 h-24 object-cover rounded-md cursor-pointer hover:opacity-90 transition-opacity bg-gray-100"
          onClick={() => !imageError && setIsOpen(true)}
          onError={() => setImageError(true)}
        />
      </div>
      
      {!imageError && isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div 
            className="bg-white rounded-lg p-4 m-4 overflow-hidden"
            style={{
              width: '90%',
              height: '90%',
              maxWidth: '90%',
              maxHeight: '90%'
            }}
          >
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-medium">Image {index + 1}</h2>
              <Button 
                variant="ghost" 
                size="icon"
                className="rounded-full h-8 w-8"
                onClick={() => setIsOpen(false)}
                title="Close"
              >
                <span className="text-xl font-bold">×</span>
              </Button>
            </div>
            
            {/* Image container with zoom applied */}
            <div 
              ref={containerRef}
              className="relative w-full h-[calc(100%-40px)] bg-gray-100 rounded-md flex justify-center items-center"
              style={{ 
                overflow: "auto"
              }}
            >
              <img
                src={image}
                alt={`Generated image ${index + 1} (full size)`}
                style={{ 
                  transform: `translate(${position.x}px, ${position.y}px) scale(${zoomLevel})`,
                  transformOrigin: 'center center',
                  transition: isDragging ? 'none' : 'transform 0.2s ease-in-out',
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: 'contain',
                  cursor: isDragging ? 'grabbing' : (zoomLevel > 1 ? 'grab' : 'default')
                }}
                className="rounded-md w-auto h-auto"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
              />
              
              {/* Zoom controls inside the container */}
              <div className="absolute bottom-4 right-4 flex items-center gap-2 bg-white p-2 rounded-full shadow-lg z-10">
                <Button 
                  variant="ghost" 
                  size="icon"
                  className="rounded-full bg-primary text-primary-foreground hover:bg-primary/90 h-10 w-10"
                  onClick={(e) => {
                    e.stopPropagation();
                    zoomOut();
                  }}
                  disabled={zoomLevel <= 0.5}
                  title="Zoom Out"
                >
                  <span className="text-xl font-bold">−</span>
                </Button>
                <span className="px-2 bg-white rounded-md text-sm font-medium">
                  {Math.round(zoomLevel * 100)}%
                </span>
                <Button 
                  variant="ghost" 
                  size="icon"
                  className="rounded-full bg-primary text-primary-foreground hover:bg-primary/90 h-10 w-10"
                  onClick={(e) => {
                    e.stopPropagation();
                    zoomIn();
                  }}
                  disabled={zoomLevel >= 3}
                  title="Zoom In"
                >
                  <span className="text-xl font-bold">+</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
