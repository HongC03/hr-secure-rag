import { TEXT } from '../constants.ts'
import type { AnswerResponse } from '../types.ts'

interface AnswerProps {
  data: AnswerResponse | null
}

export default function Answer({ data }: AnswerProps) {
  if (!data) return <div className="answer">{TEXT.query.emptyAnswer}</div>

  return (
    <div className={`answer ${data.status || ''}`}>
      <small>
        {data.status?.toUpperCase() ?? ''}{' '}
        {data.correlationId ? TEXT.query.correlationId(data.correlationId) : ''}
      </small>
      <p>{data.answer || data.error || ''}</p>
      {data.citations?.length > 0 && (
        <div className="citations">
          {data.citations.map((citation) => (
            <span key={citation.id}>
              {citation.title} <i>{citation.classification}</i>
            </span>
          ))}
        </div>
      )}
      <em>
        {[data.pipeline, ...(data.controls || [])]
          .filter(Boolean)
          .join(TEXT.query.pipelineSeparator)}
      </em>
    </div>
  )
}
