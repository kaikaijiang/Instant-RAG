import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useEmailStore, EmailSummary } from "@/hooks/useEmailStore";
import { useToast } from "@/hooks/use-toast";

interface EmailSummarizationProps {
  projectId: string;
}

export default function EmailSummarization({ projectId }: EmailSummarizationProps) {
  const { processingStatus, emailSummaries, summarizeEmails } = useEmailStore();
  const { toast } = useToast();
  const [isSummarizing, setIsSummarizing] = useState(false);

  const handleSummarize = async () => {
    setIsSummarizing(true);
    toast({
      title: "Summarizing emails...",
      variant: "default",
    });
    
    try {
      await summarizeEmails();
      toast({
        title: "Summarization complete!",
        variant: "success",
      });
    } catch (error) {
      console.error("Error summarizing emails:", error);
      toast({
        title: "Failed to summarize emails",
        variant: "destructive",
      });
    } finally {
      setIsSummarizing(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Summarization</CardTitle>
        <CardDescription>
          Generate summaries of your emails for better understanding and embedding.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button 
          onClick={handleSummarize} 
          disabled={isSummarizing || processingStatus.summarizingEmails}
        >
          {isSummarizing || processingStatus.summarizingEmails ? "Summarizing..." : "Summarize Emails"}
        </Button>
        
        {emailSummaries.length > 0 && (
          <div className="mt-4 space-y-4">
            <h3 className="text-sm font-medium">Email Summaries</h3>
            <div className="space-y-3">
              {emailSummaries.map((summary) => (
                <SummaryItem key={summary.id} summary={summary} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SummaryItem({ summary }: { summary: EmailSummary }) {
  return (
    <div className="rounded-md border p-3 text-sm">
      <div className="flex justify-between items-start mb-2">
        <span className="font-medium">Email Summary</span>
        <span className="text-xs text-muted-foreground">
          {new Date(summary.timestamp).toLocaleString()}
        </span>
      </div>
      <p className="text-muted-foreground">{summary.summary}</p>
    </div>
  );
}
