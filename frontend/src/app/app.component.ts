import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { ChatComponent } from './components/chat/chat.component';
import { DocumentUploadComponent } from './components/document-upload/document-upload.component';
import { OrderManagementComponent } from './components/order-management/order-management.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ChatComponent, DocumentUploadComponent, OrderManagementComponent],
  template: `
    <div class="app-container">
      <header class="app-header">
        <h1>Omni-Help</h1>
        <p class="subtitle">Intelligent Customer Support Platform</p>
      </header>
      
      <nav class="app-nav">
        <a routerLink="/chat" routerLinkActive="active">Chat</a>
        <a routerLink="/documents" routerLinkActive="active">Documents</a>
        <a routerLink="/orders" routerLinkActive="active">Orders</a>
      </nav>
      
      <main class="app-main">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    
    .app-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
      
      h1 {
        font-size: 2.5em;
        margin-bottom: 10px;
      }
      
      .subtitle {
        font-size: 1.1em;
        opacity: 0.9;
      }
    }
    
    .app-nav {
      background: white;
      padding: 15px 30px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      display: flex;
      gap: 20px;
      
      a {
        text-decoration: none;
        color: #333;
        padding: 10px 20px;
        border-radius: 5px;
        transition: all 0.3s ease;
        
        &:hover, &.active {
          background-color: #667eea;
          color: white;
        }
      }
    }
    
    .app-main {
      flex: 1;
      padding: 30px;
    }
  `]
})
export class AppComponent {
  title = 'Omni-Help';
}

