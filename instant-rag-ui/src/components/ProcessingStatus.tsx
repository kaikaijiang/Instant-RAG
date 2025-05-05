import React from "react";
import { CheckIcon } from "lucide-react";
import { Spinner } from "@/components/ui/spinner";
import { ProcessingStatus as ProcessingStatusType } from "@/hooks/useEmailStore";

interface ProcessingStatusItemProps {
  label: string;
  isProcessing: boolean;
  isCompleted: boolean;
}

function ProcessingStatusItem({ 
  label, 
  isProcessing, 
  isCompleted 
}: ProcessingStatusItemProps) {
  return (
    <div className="flex items-center gap-2 py-1.5">
      <div className="w-6 h-6 flex items-center justify-center">
        {isProcessing ? (
          <Spinner size="sm" />
        ) : isCompleted ? (
          <CheckIcon className="h-5 w-5 text-green-500" />
        ) : (
          <div className="h-2 w-2 rounded-full bg-gray-300" />
        )}
      </div>
      <span className={isProcessing ? "font-medium" : "text-muted-foreground"}>
        {label}
      </span>
    </div>
  );
}

interface ProcessingStatusProps {
  status: ProcessingStatusType;
  completedSteps: {
    uploadingDocuments: boolean;
    embeddingDocuments: boolean;
    fetchingEmails: boolean;
    summarizingEmails: boolean;
  };
}

export default function ProcessingStatus({ 
  status, 
  completedSteps 
}: ProcessingStatusProps) {
  return (
    <div className="space-y-1">
      <ProcessingStatusItem
        label="Uploading Documents"
        isProcessing={status.uploadingDocuments}
        isCompleted={completedSteps.uploadingDocuments}
      />
      <ProcessingStatusItem
        label="Embedding Documents"
        isProcessing={status.embeddingDocuments}
        isCompleted={completedSteps.embeddingDocuments}
      />
      <ProcessingStatusItem
        label="Fetching Emails"
        isProcessing={status.fetchingEmails}
        isCompleted={completedSteps.fetchingEmails}
      />
      <ProcessingStatusItem
        label="Summarizing Emails"
        isProcessing={status.summarizingEmails}
        isCompleted={completedSteps.summarizingEmails}
      />
    </div>
  );
}
