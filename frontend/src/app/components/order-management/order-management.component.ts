import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-order-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="order-container">
      <div class="card">
        <h2>Order Management</h2>
        
        <div class="tabs">
          <button 
            [class.active]="activeTab === 'create'"
            (click)="activeTab = 'create'">
            Create Order
          </button>
          <button 
            [class.active]="activeTab === 'search'"
            (click)="activeTab = 'search'">
            Search Orders
          </button>
        </div>
        
        <!-- Create Order Tab -->
        <div *ngIf="activeTab === 'create'" class="tab-content">
          <form (ngSubmit)="createOrder()">
            <div class="form-group">
              <label>Order ID</label>
              <input [(ngModel)]="newOrder.order_id" name="order_id" required />
            </div>
            
            <div class="form-group">
              <label>Customer ID</label>
              <input [(ngModel)]="newOrder.customer_id" name="customer_id" required />
            </div>
            
            <div class="form-group">
              <label>Product Name</label>
              <input [(ngModel)]="newOrder.product_name" name="product_name" required />
            </div>
            
            <div class="form-group">
              <label>Product Model</label>
              <input [(ngModel)]="newOrder.product_model" name="product_model" />
            </div>
            
            <div class="form-group">
              <label>Order Date</label>
              <input type="date" [(ngModel)]="newOrder.order_date" name="order_date" required />
            </div>
            
            <div class="form-group">
              <label>Status</label>
              <select [(ngModel)]="newOrder.status" name="status" required>
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="shipped">Shipped</option>
                <option value="delivered">Delivered</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Total Amount</label>
              <input type="number" step="0.01" [(ngModel)]="newOrder.total_amount" name="total_amount" required />
            </div>
            
            <button type="submit" class="btn btn-primary">Create Order</button>
          </form>
        </div>
        
        <!-- Search Orders Tab -->
        <div *ngIf="activeTab === 'search'" class="tab-content">
          <div class="search-form">
            <input 
              type="text" 
              [(ngModel)]="searchCustomerId" 
              placeholder="Enter Customer ID"
              class="search-input"
            />
            <button (click)="searchOrders()" class="btn btn-primary">Search</button>
          </div>
          
          <div *ngIf="orders.length > 0" class="orders-list">
            <div *ngFor="let order of orders" class="order-card">
              <h3>Order #{{ order.order_id }}</h3>
              <p><strong>Product:</strong> {{ order.product_name }}</p>
              <p><strong>Status:</strong> {{ order.status }}</p>
              <p><strong>Amount:</strong> ${{ order.total_amount }}</p>
              <p><strong>Date:</strong> {{ order.order_date }}</p>
            </div>
          </div>
          
          <div *ngIf="orders.length === 0 && searched" class="no-orders">
            No orders found for this customer.
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .order-container {
      max-width: 900px;
      margin: 0 auto;
    }
    
    .tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      border-bottom: 2px solid #eee;
      
      button {
        padding: 10px 20px;
        border: none;
        background: none;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        
        &.active {
          border-bottom-color: #667eea;
          color: #667eea;
          font-weight: bold;
        }
      }
    }
    
    .tab-content {
      padding: 20px 0;
    }
    
    .form-group {
      margin-bottom: 20px;
      
      label {
        display: block;
        margin-bottom: 5px;
        font-weight: 500;
      }
      
      input, select {
        width: 100%;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
      }
    }
    
    .search-form {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      
      .search-input {
        flex: 1;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
      }
    }
    
    .orders-list {
      display: grid;
      gap: 15px;
    }
    
    .order-card {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 8px;
      border-left: 4px solid #667eea;
      
      h3 {
        margin-bottom: 10px;
        color: #667eea;
      }
      
      p {
        margin: 5px 0;
      }
    }
    
    .no-orders {
      text-align: center;
      padding: 40px;
      color: #666;
    }
  `]
})
export class OrderManagementComponent {
  activeTab: 'create' | 'search' = 'create';
  newOrder: any = {
    order_id: '',
    customer_id: '',
    product_name: '',
    product_model: '',
    order_date: new Date().toISOString().split('T')[0],
    status: 'pending',
    total_amount: 0
  };
  searchCustomerId: string = '';
  orders: any[] = [];
  searched: boolean = false;

  constructor(private apiService: ApiService) {}

  createOrder() {
    this.apiService.createOrder(this.newOrder).subscribe({
      next: (response) => {
        alert('Order created successfully!');
        this.newOrder = {
          order_id: '',
          customer_id: '',
          product_name: '',
          product_model: '',
          order_date: new Date().toISOString().split('T')[0],
          status: 'pending',
          total_amount: 0
        };
      },
      error: (error) => {
        alert('Error creating order: ' + (error.error?.detail || 'Unknown error'));
      }
    });
  }

  searchOrders() {
    if (!this.searchCustomerId.trim()) return;

    this.apiService.getCustomerOrders(this.searchCustomerId).subscribe({
      next: (response) => {
        this.orders = response;
        this.searched = true;
      },
      error: (error) => {
        alert('Error searching orders: ' + (error.error?.detail || 'Unknown error'));
        this.orders = [];
        this.searched = true;
      }
    });
  }
}

