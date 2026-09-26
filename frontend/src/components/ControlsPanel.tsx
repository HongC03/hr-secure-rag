import { TEXT } from '../constants.ts'

export default function ControlsPanel() {
  return (
    <aside className="card controls">
      <div className="title">
        {TEXT.controls.heading} <label>{TEXT.controls.label}</label>
      </div>
      {TEXT.controls.items.map((item) => (
        <div className="control" key={item.number}>
          <b>{item.number}</b>
          <span>
            <strong>{item.title}</strong>
            {item.description}
          </span>
        </div>
      ))}
    </aside>
  )
}
