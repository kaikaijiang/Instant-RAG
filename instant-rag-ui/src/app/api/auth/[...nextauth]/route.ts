import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { API_CONFIG } from "@/services/api";

// Test user for development
const TEST_USER = {
  id: "test-user-id",
  email: "test@example.com",
  token: "test-token"
};

// Define the authentication handler
const handler = NextAuth({
  secret: process.env.NEXTAUTH_SECRET,
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        // For testing: allow a hardcoded test user
        if (credentials.email === "test@example.com" && credentials.password === "password123") {
          console.log("Using test user for authentication");
          return TEST_USER;
        }

        try {
          // Call the backend API for authentication
          const response = await fetch(`${API_CONFIG.baseUrl}/auth/login`, {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
              username: credentials.email, // FastAPI OAuth2PasswordRequestForm expects 'username'
              password: credentials.password,
            }),
          });

          if (!response.ok) {
            console.error("Authentication failed:", response.statusText);
            return null;
          }

          const data = await response.json();

          // Return the user object with token
          return {
            id: credentials.email,
            email: credentials.email,
            token: data.access_token,
          };
        } catch (error) {
          console.error("Authentication error:", error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    // Include the token in the JWT
    async jwt({ token, user }) {
      if (user) {
        token.email = user.email;
        token.token = user.token;
      }
      console.log('JWT callback - token:', { ...token, token: token.token ? `${token.token.substring(0, 10)}...` : 'undefined' });
      return token;
    },
    // Make the token available in the client session
    async session({ session, token }) {
      if (token) {
        session.user = {
          ...session.user,
          email: token.email || '',
        };
        session.token = token.token;
      }
      console.log('Session callback - session:', { 
        ...session, 
        token: session.token ? `${session.token.substring(0, 10)}...` : 'undefined' 
      });
      return session;
    },
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours
  },
});

export { handler as GET, handler as POST };
