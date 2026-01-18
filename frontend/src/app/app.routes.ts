import { Routes } from '@angular/router';
import { ChatComponent } from './components/chat/chat.component';
import { DocumentUploadComponent } from './components/document-upload/document-upload.component';
import { OrderManagementComponent } from './components/order-management/order-management.component';

export const routes: Routes = [
  { path: '', redirectTo: '/chat', pathMatch: 'full' },
  { path: 'chat', component: ChatComponent },
  { path: 'documents', component: DocumentUploadComponent },
  { path: 'orders', component: OrderManagementComponent }
];

