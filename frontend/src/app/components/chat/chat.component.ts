import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, ChatRequest, ChatResponse } from '../../services/api.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="chat-container">
      <div class="chat-header">
        <h2>Chat with Omni-Help</h2>
        <p class="intent-info" *ngIf="lastIntent">
          Intent: <span [class]="'intent-' + lastIntent">{{ lastIntent }}</span> 
          → <span class="route-info">{{ lastRoute }}</span>
        </p>
      </div>
      
      <div class="chat-messages" #messagesContainer>
        <div *ngFor="let message of messages" [class]="'message ' + message.type">
          <div class="message-content">
            <p>{{ message.content }}</p>
            <span class="message-time">{{ message.timestamp | date:'short' }}</span>
          </div>
        </div>
        <div *ngIf="loading" class="message bot loading">
          <div class="message-content">
            <p>Thinking...</p>
          </div>
        </div>
      </div>
      
      <div class="chat-input">
        <form (ngSubmit)="sendMessage()">
          <input 
            type="text" 
            [(ngModel)]="userQuery" 
            name="userQuery"
            placeholder="Ask a question about orders, product manuals, or policies..."
            [disabled]="loading"
            class="input-field"
          />
          <button type="submit" [disabled]="loading || !userQuery.trim()" class="send-button">
            Send
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .chat-container {
      max-width: 900px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      height: calc(100vh - 200px);
      background: white;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .chat-header {
      padding: 20px;
      border-bottom: 1px solid #eee;
      
      h2 {
        margin-bottom: 10px;
      }
      
      .intent-info {
        font-size: 0.9em;
        color: #666;
        
        .intent-policy_document {
          color: #28a745;
          font-weight: bold;
        }
        
        .intent-order_tracking {
          color: #007bff;
          font-weight: bold;
        }
        
        .intent-general {
          color: #ffc107;
          font-weight: bold;
        }
        
        .route-info {
          color: #6c757d;
          font-style: italic;
        }
      }
    }
    
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 15px;
    }
    
    .message {
      max-width: 70%;
      
      &.user {
        align-self: flex-end;
        
        .message-content {
          background: #667eea;
          color: white;
        }
      }
      
      &.bot {
        align-self: flex-start;
        
        .message-content {
          background: #f0f0f0;
          color: #333;
        }
      }
      
      &.loading {
        .message-content {
          background: #e9ecef;
          font-style: italic;
        }
      }
    }
    
    .message-content {
      padding: 12px 16px;
      border-radius: 18px;
      
      p {
        margin: 0;
        line-height: 1.5;
      }
      
      .message-time {
        font-size: 0.75em;
        opacity: 0.7;
        margin-top: 5px;
        display: block;
      }
    }
    
    .chat-input {
      padding: 20px;
      border-top: 1px solid #eee;
      
      form {
        display: flex;
        gap: 10px;
      }
      
      .input-field {
        flex: 1;
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 25px;
        font-size: 14px;
        
        &:focus {
          outline: none;
          border-color: #667eea;
        }
      }
      
      .send-button {
        padding: 12px 30px;
        background: #667eea;
        color: white;
        border: none;
        border-radius: 25px;
        cursor: pointer;
        font-weight: 500;
        
        &:hover:not(:disabled) {
          background: #5568d3;
        }
        
        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      }
    }
  `]
})
export class ChatComponent {
  userQuery: string = '';
  messages: Array<{type: string, content: string, timestamp: Date}> = [];
  loading: boolean = false;
  lastIntent: string = '';
  lastRoute: string = '';

  constructor(private apiService: ApiService) {}

  sendMessage() {
    if (!this.userQuery.trim() || this.loading) return;

    const userMessage = this.userQuery;
    this.messages.push({
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    });

    this.userQuery = '';
    this.loading = true;

    const request: ChatRequest = {
      query: userMessage
    };

    this.apiService.chatQuery(request).subscribe({
      next: (response: ChatResponse) => {
        this.messages.push({
          type: 'bot',
          content: response.answer,
          timestamp: new Date()
        });
        this.lastIntent = response.intent;
        this.lastRoute = response.route_to;
        this.loading = false;
      },
      error: (error) => {
        this.messages.push({
          type: 'bot',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date()
        });
        this.loading = false;
        console.error('Chat error:', error);
      }
    });
  }
}

