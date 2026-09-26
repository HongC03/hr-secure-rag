import { useState } from 'react'
import { TEXT } from '../constants.ts'
import type { AnswerResponse, User } from '../types.ts'
import Answer from './Answer.tsx'

interface QueryPanelProps {
  user: User
  busy: boolean
  answer: AnswerResponse | null
  onAsk: (question: string) => Promise<void>
}

export default function QueryPanel({
  user,
  busy,
  answer,
  onAsk,
}: QueryPanelProps) {
  const [question, setQuestion] = useState(TEXT.query.defaultQuestion)

  return (
    <article className="card query">
      <div className="title">
        {TEXT.query.heading} <label>{TEXT.query.userLabel(user)}</label>
      </div>
      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        aria-label={TEXT.query.questionLabel}
        disabled={!user}
      />
      <div>
        <button onClick={() => onAsk(question)} disabled={busy || !user}>
          {busy ? TEXT.query.processing : TEXT.query.retrieve}{' '}
          <b>{TEXT.query.arrow}</b>
        </button>
        <button
          className="outline"
          onClick={() => setQuestion(TEXT.query.boundaryQuestion)}
          disabled={!user}
        >
          {TEXT.query.testBoundary}
        </button>
      </div>
      <Answer data={answer} />
    </article>
  )
}
