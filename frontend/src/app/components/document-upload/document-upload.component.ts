import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-document-upload',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="upload-container">
      <div class="card">
        <h2>Upload Product Manuals</h2>
        <p class="description">Upload PDF documents to be indexed in the vector database for RAG queries.</p>
        
        <div class="upload-area" 
             (dragover)="onDragOver($event)"
             (dragleave)="onDragLeave($event)"
             (drop)="onDrop($event)"
             [class.drag-over]="isDragOver">
          <input 
            type="file" 
            #fileInput 
            accept=".pdf" 
            (change)="onFileSelected($event)"
            style="display: none"
          />
          
          <div *ngIf="!selectedFile" class="upload-placeholder">
            <p>📄 Drag and drop a PDF file here</p>
            <p>or</p>
            <button (click)="fileInput.click()" class="btn btn-primary">Browse Files</button>
          </div>
          
          <div *ngIf="selectedFile" class="file-info">
            <p><strong>Selected:</strong> {{ selectedFile.name }}</p>
            <p><strong>Size:</strong> {{ formatFileSize(selectedFile.size) }}</p>
            <div class="file-actions">
              <button (click)="uploadFile()" [disabled]="uploading" class="btn btn-primary">
                {{ uploading ? 'Uploading...' : 'Upload' }}
              </button>
              <button (click)="clearFile()" [disabled]="uploading" class="btn btn-secondary">Clear</button>
            </div>
          </div>
        </div>
        
        <div *ngIf="uploadResult" class="upload-result" [class.success]="uploadResult.success">
          <p *ngIf="uploadResult.success">
            ✅ {{ uploadResult.message }}<br>
            <small>Processed {{ uploadResult.chunks }} chunks</small>
          </p>
          <p *ngIf="!uploadResult.success">
            ❌ {{ uploadResult.message }}
          </p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .upload-container {
      max-width: 800px;
      margin: 0 auto;
    }
    
    .card {
      padding: 30px;
    }
    
    h2 {
      margin-bottom: 10px;
    }
    
    .description {
      color: #666;
      margin-bottom: 30px;
    }
    
    .upload-area {
      border: 2px dashed #ddd;
      border-radius: 10px;
      padding: 40px;
      text-align: center;
      transition: all 0.3s ease;
      
      &.drag-over {
        border-color: #667eea;
        background-color: #f0f4ff;
      }
    }
    
    .upload-placeholder {
      p {
        margin: 10px 0;
        color: #666;
      }
    }
    
    .file-info {
      p {
        margin: 10px 0;
      }
      
      .file-actions {
        margin-top: 20px;
        display: flex;
        gap: 10px;
        justify-content: center;
      }
    }
    
    .upload-result {
      margin-top: 20px;
      padding: 15px;
      border-radius: 5px;
      background: #f8f9fa;
      
      &.success {
        background: #d4edda;
        color: #155724;
      }
      
      small {
        display: block;
        margin-top: 5px;
        opacity: 0.8;
      }
    }
  `]
})
export class DocumentUploadComponent {
  selectedFile: File | null = null;
  isDragOver: boolean = false;
  uploading: boolean = false;
  uploadResult: any = null;

  constructor(private apiService: ApiService) {}

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.selectedFile = files[0];
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
    }
  }

  clearFile() {
    this.selectedFile = null;
    this.uploadResult = null;
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  uploadFile() {
    if (!this.selectedFile) return;

    this.uploading = true;
    this.uploadResult = null;

    this.apiService.uploadDocument(this.selectedFile).subscribe({
      next: (response) => {
        this.uploadResult = {
          success: true,
          message: response.message,
          chunks: response.chunks
        };
        this.uploading = false;
        this.selectedFile = null;
      },
      error: (error) => {
        this.uploadResult = {
          success: false,
          message: error.error?.detail || 'Upload failed. Please try again.'
        };
        this.uploading = false;
      }
    });
  }
}

