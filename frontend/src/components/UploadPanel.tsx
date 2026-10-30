import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client.ts'
import { API_PATHS, ROUTES, UPLOAD_MAX_BYTES } from '../constants.ts'
import type {
  UploadedDocument,
  UploadListResponse,
  UploadResponse,
} from '../types.ts'

interface UploadPanelProps {
  busy: boolean
  onBusyChange: (busy: boolean) => void
}

export default function UploadPanel({ busy, onBusyChange }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null)
  const [documents, setDocuments] = useState<UploadedDocument[]>([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api<UploadListResponse>(API_PATHS.uploads)
      .then((data) => setDocuments(data.documents))
      .catch((error) => setError(getErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const validate = (selected: File | null) => {
    setFile(selected)
    setSuccess('')
    if (!selected) return setError('')
    if (!/\.(txt|md)$/i.test(selected.name)) {
      setError('Only .txt and .md files are supported.')
    } else if (selected.size > UPLOAD_MAX_BYTES) {
      setError('Files must be at most 1 MB.')
    } else if (selected.size === 0) {
      setError('Choose a non-empty file.')
    } else {
      setError('')
    }
  }

  const upload = async (form: HTMLFormElement) => {
    if (!file || busy) return
    onBusyChange(true)
    setError('')
    setSuccess('')
    try {
      const data = await api<UploadResponse>(API_PATHS.uploads, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/octet-stream',
          'X-File-Name': encodeURIComponent(file.name),
        },
        body: file,
      })
      setDocuments((previous) => [...previous, data.document])
      setSuccess(`${data.document.title} was uploaded and is ready to query.`)
      setFile(null)
      form.reset()
    } catch (error) {
      setError(getErrorMessage(error))
    } finally {
      onBusyChange(false)
    }
  }

  return (
    <section className="grid uploadGrid">
      <div className="card">
        <div className="title">
          <span>Upload a document</span>
          <label>PRIVATE TO YOU</label>
        </div>
        <p className="muted">
          Upload UTF-8 text or Markdown files, up to 1 MB each.
        </p>
        <form
          className="uploadForm"
          onSubmit={(event) => {
            event.preventDefault()
            void upload(event.currentTarget)
          }}
        >
          <label htmlFor="upload-file">Choose a file</label>
          <input
            id="upload-file"
            name="file"
            type="file"
            accept=".txt,.md"
            required
            disabled={busy}
            aria-describedby="upload-help"
            onChange={(event) => validate(event.target.files?.[0] ?? null)}
          />
          <p id="upload-help" className="muted">
            Only your account can retrieve this document. Use synthetic HR data
            in this demo.
          </p>
          {error && (
            <p className="loginError" role="alert">
              {error}
            </p>
          )}
          {success && (
            <p className="uploadSuccess" role="status">
              {success}
            </p>
          )}
          <button
            type="submit"
            disabled={
              busy ||
              !file ||
              file.size === 0 ||
              file.size > UPLOAD_MAX_BYTES ||
              !/\.(txt|md)$/i.test(file.name)
            }
          >
            {busy ? 'Uploading and indexing…' : 'Upload document'}
          </button>
        </form>
      </div>
      <div className="card">
        <div className="title">
          <span>Your uploaded documents</span>
        </div>
        <p className="muted">
          Saved documents remain available after you sign in again.
        </p>
        {loading ? (
          <p className="muted">Loading documents…</p>
        ) : documents.length === 0 ? (
          <p className="muted">You have not uploaded any documents yet.</p>
        ) : (
          <ul className="uploadList">
            {documents.map((document) => (
              <li key={document.id}>
                <strong>{document.title}</strong>
                <span>{document.classification}</span>
              </li>
            ))}
          </ul>
        )}
        <a className="pageLink" href={ROUTES.home}>
          Ask a question about your documents →
        </a>
      </div>
    </section>
  )
}
