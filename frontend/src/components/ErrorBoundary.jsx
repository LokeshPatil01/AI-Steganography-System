import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '40px 24px',
          margin: '24px auto',
          maxWidth: '700px',
          background: 'rgba(244, 63, 94, 0.08)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: '16px',
          textAlign: 'center',
          color: '#fff',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }}>
          <AlertTriangle size={48} color="#f43f5e" style={{ margin: '0 auto 16px' }} />
          <h2 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '8px', color: '#f43f5e' }}>
            Component Render Exception Caught
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
            An unexpected error occurred while rendering this tab view. The rest of the application remains protected.
          </p>
          <div style={{
            background: 'rgba(0,0,0,0.4)',
            padding: '12px 16px',
            borderRadius: '8px',
            textAlign: 'left',
            fontFamily: 'monospace',
            fontSize: '12px',
            color: '#fca5a5',
            overflowX: 'auto',
            marginBottom: '20px',
            border: '1px solid rgba(244, 63, 94, 0.2)',
          }}>
            {this.state.error ? this.state.error.toString() : 'Unknown Error'}
          </div>
          <button
            type="button"
            onClick={this.handleReset}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              background: 'var(--gradient-cyber)',
              color: '#fff',
              fontWeight: '700',
              fontSize: '13px',
              border: 'none',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <RefreshCw size={14} /> Reset & Reload View
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
