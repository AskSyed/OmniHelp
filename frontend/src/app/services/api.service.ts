import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ChatRequest {
  query: string;
  conversation_id?: string;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  route_to: string;
  sources: string[];
  error?: string;
}

export interface DocumentUploadResponse {
  message: string;
  filename: string;
  chunks: number;
  document_id: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  chatQuery(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat/query`, request);
  }

  uploadDocument(file: File): Observable<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<DocumentUploadResponse>(`${this.apiUrl}/documents/upload`, formData);
  }

  listDocuments(): Observable<any> {
    return this.http.get(`${this.apiUrl}/documents/list`);
  }

  createOrder(order: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/orders/`, order);
  }

  getOrder(orderId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/orders/${orderId}`);
  }

  getCustomerOrders(customerId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/orders/customer/${customerId}`);
  }
}

