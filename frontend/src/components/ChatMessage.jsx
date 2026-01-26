import './ChatMessage.css'

function ChatMessage({ message }) {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className={`message ${message.type} ${message.isError ? 'error' : ''}`}>
      <div className="message-content">
        <p>{message.content}</p>
        
        {message.sources && message.sources.length > 0 && (
          <div className="sources">
            <div className="sources-title">Sources:</div>
            {message.sources.map((source, index) => (
              <span key={index} className="source-item">
                {source}
              </span>
            ))}
          </div>
        )}

        <div className="message-time">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  )
}

export default ChatMessage
