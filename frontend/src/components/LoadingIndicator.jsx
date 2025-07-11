// Simple loading animation component
export default function LoadingIndicator() {
  return (
    <div className="loading-indicator">
      <div className="loading-dots">
        <span className="dot"></span>
        <span className="dot"></span>
        <span className="dot"></span>
      </div>
    </div>
  );
}