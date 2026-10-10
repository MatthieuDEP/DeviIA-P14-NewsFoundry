import ReactMarkdown from "react-markdown";
import RobotIcon from "./RobotIcon";
import styles from "./ChatWorkspace.module.css";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <article className={`${styles.messageRow} ${isUser ? styles.userRow : ""}`} aria-label={isUser ? "Votre message" : "Réponse de l’assistant"}>
      <span className={`${styles.avatar} ${isUser ? styles.userAvatar : ""}`}>
        {isUser ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
            <circle cx="12" cy="8" r="3" /><path d="M5 21v-3a7 7 0 0 1 14 0v3" />
          </svg>
        ) : <RobotIcon size={18} />}
      </span>
      <div className={`${styles.bubble} ${isUser ? styles.userBubble : ""}`}>
        <span className={styles.srOnly}>{isUser ? "Vous" : "Assistant"}</span>
        <div className={styles.messageText}>
          {isUser ? <p>{message.content}</p> : (
            <ReactMarkdown skipHtml components={{
              h1: ({ children }) => <h2>{children}</h2>,
              a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
            }}>{message.content}</ReactMarkdown>
          )}
        </div>
        <time className={styles.timestamp} dateTime={message.timestamp}>
          {new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" }).format(new Date(message.timestamp))}
        </time>
      </div>
    </article>
  );
}
