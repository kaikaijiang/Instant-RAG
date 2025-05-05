import { useState } from "react";
import { toast } from "react-hot-toast";
import { connectToEmailServer } from "@/services/api";
import { useProjectStore } from "@/hooks/useProjectStore";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DatePicker } from "@/components/ui/date-picker";
import { Form, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { useEmailStore, FetchedEmail } from "@/hooks/useEmailStore";

interface EmailSetupProps {
  projectId: string;
}

export default function EmailSetup({ projectId }: EmailSetupProps) {
  console.log("EmailSetup component rendered", projectId);
  const { 
    emailSettings, 
    updateEmailSettings, 
    isConnecting, 
    setIsConnecting, 
    setConnectionError,
    fetchedEmails,
    setFetchedEmails
  } = useEmailStore();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!emailSettings.imapServer.trim()) {
      newErrors.imapServer = "IMAP Server is required";
    }
    
    if (!emailSettings.emailAddress.trim()) {
      newErrors.emailAddress = "Email Address is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailSettings.emailAddress)) {
      newErrors.emailAddress = "Please enter a valid email address";
    }
    
    if (!emailSettings.password.trim()) {
      newErrors.password = "Password is required";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string, value: string) => {
    updateEmailSettings({ [field]: value });
    
    // Clear error when user types
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleConnectAndFetch = async () => {
    if (!validateForm()) {
      return;
    }
    
    setIsConnecting(true);
    setConnectionError(null);
    
    // Show connecting toast
    toast.loading("Connecting to email server...", { id: "email-connect" });
    
    try {
      // Get the selected project ID from the project store
      const { selectedProjectId } = useProjectStore.getState();
      
      // If no project is selected, show an error message
      if (!selectedProjectId) {
        toast.error("No project selected. Please select a project first.", { id: "email-connect" });
        setConnectionError("No project selected. Please select a project first.");
        setIsConnecting(false);
        return;
      }
      
      // Call the real API function with the selected project ID
      const result = await connectToEmailServer(selectedProjectId, {
        ...emailSettings,
        startDate: emailSettings.startDate || undefined,
        endDate: emailSettings.endDate || undefined
      });
      
      if (result.success) {
        // Success toast
        toast.success(result.message || "Connected successfully!", { id: "email-connect" });
        
        // If emails were fetched, store them
        if (result.emails) {
          const fetchedEmailsList: FetchedEmail[] = result.emails.subjects.map(subject => ({
            subject,
            timestamp: new Date()
          }));
          setFetchedEmails(fetchedEmailsList);
        }
      } else {
        // Error toast
        toast.error(result.message || "Failed to connect to email server", { id: "email-connect" });
        setConnectionError(result.message || "Failed to connect to email server");
      }
    } catch (error) {
      // Error toast
      const errorMessage = error instanceof Error ? error.message : "Failed to connect to email server";
      toast.error(errorMessage, { id: "email-connect" });
      setConnectionError(errorMessage);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Setup</CardTitle>
        <CardDescription>
          Configure email settings to fetch emails for your RAG system.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormItem>
              <FormLabel required>IMAP Server</FormLabel>
              <FormControl>
                <Input
                  placeholder="imap.example.com"
                  value={emailSettings.imapServer}
                  onChange={(e) => handleInputChange("imapServer", e.target.value)}
                />
              </FormControl>
              {errors.imapServer && <FormMessage>{errors.imapServer}</FormMessage>}
            </FormItem>
            
            <FormItem>
              <FormLabel required>Email Address</FormLabel>
              <FormControl>
                <Input
                  placeholder="you@example.com"
                  value={emailSettings.emailAddress}
                  onChange={(e) => handleInputChange("emailAddress", e.target.value)}
                />
              </FormControl>
              {errors.emailAddress && <FormMessage>{errors.emailAddress}</FormMessage>}
            </FormItem>
            
            <FormItem>
              <FormLabel required>Password</FormLabel>
              <FormControl>
                <Input
                  type="password"
                  placeholder="Your email password"
                  value={emailSettings.password}
                  onChange={(e) => handleInputChange("password", e.target.value)}
                />
              </FormControl>
              {errors.password && <FormMessage>{errors.password}</FormMessage>}
            </FormItem>
            
            <FormItem>
              <FormLabel>Sender Filter (Optional)</FormLabel>
              <FormControl>
                <Input
                  placeholder="Filter by sender email"
                  value={emailSettings.senderFilter}
                  onChange={(e) => handleInputChange("senderFilter", e.target.value)}
                />
              </FormControl>
            </FormItem>
            
            <FormItem>
              <FormLabel>Subject Keywords (Optional)</FormLabel>
              <FormControl>
                <Input
                  placeholder="Keywords separated by commas"
                  value={emailSettings.subjectKeywords}
                  onChange={(e) => handleInputChange("subjectKeywords", e.target.value)}
                />
              </FormControl>
            </FormItem>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormItem>
              <FormLabel>Start Date (Optional)</FormLabel>
              <FormControl>
                <DatePicker
                  value={emailSettings.startDate || ""}
                  onChange={(e) => handleInputChange("startDate", e.target.value)}
                />
              </FormControl>
            </FormItem>
            
            <FormItem>
              <FormLabel>End Date (Optional)</FormLabel>
              <FormControl>
                <DatePicker
                  value={emailSettings.endDate || ""}
                  onChange={(e) => handleInputChange("endDate", e.target.value)}
                />
              </FormControl>
            </FormItem>
          </div>
          
          <Button
            className="w-full"
            onClick={handleConnectAndFetch}
            disabled={isConnecting}
          >
            {isConnecting ? "Connecting..." : "Connect and Fetch Emails"}
          </Button>
        </Form>
        
        {fetchedEmails.length > 0 && (
          <div className="mt-6 border-t pt-4">
            <h3 className="text-sm font-medium mb-3">Fetched Emails ({fetchedEmails.length})</h3>
            <div className="max-h-60 overflow-y-auto space-y-2">
              {fetchedEmails.map((email, index) => (
                <div 
                  key={index} 
                  className="p-2 bg-muted rounded-md text-sm"
                >
                  <div className="font-medium truncate">{email.subject}</div>
                  <div className="text-xs text-muted-foreground">
                    {email.timestamp.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
