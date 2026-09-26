import { TEXT } from '../constants.ts'
import type { AuditEvent } from '../types.ts'

interface AuditPanelProps {
  events: AuditEvent[]
}

export default function AuditPanel({ events }: AuditPanelProps) {
  return (
    <section className="card auditCard">
      <div className="title">
        {TEXT.audit.heading} <label>{TEXT.audit.label}</label>
      </div>
      {events.length ? (
        <div>
          {events
            .slice()
            .reverse()
            .map((event) => (
              <div className="event" key={event.correlation_id}>
                <b>{event.action}</b>
                <span>{TEXT.audit.summary(event)}</span>
              </div>
            ))}
        </div>
      ) : (
        <p className="muted">{TEXT.audit.empty}</p>
      )}
    </section>
  )
}
