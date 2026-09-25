import { useEffect, useState } from "react";
import { api } from "../api/client";
type O = { id: number; label: string; capacity_note: string; preheat_min: number };
export default function OvensPage() {
  const [rows, setRows] = useState<O[]>([]);
  const [draft, setDraft] = useState<Record<number, number>>({});
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => {
    api<O[]>("/ovens").then(rs => {
      setRows(rs);
      setDraft(Object.fromEntries(rs.map(o => [o.id, o.preheat_min])));
    });
  }, []);
  async function save(o: O) {
    setMsg(""); setErr("");
    try {
      const v = Math.max(0, Number(draft[o.id] ?? o.preheat_min));
      const u = await api<O>(`/ovens/${o.id}`, { method: "PATCH", body: JSON.stringify({ preheat_min: v }) });
      setRows(rs => rs.map(r => (r.id === o.id ? u : r)));
      setDraft(d => ({ ...d, [o.id]: u.preheat_min }));
      setMsg(`已保存 ${o.label}：换档预热 ${u.preheat_min} 分钟`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>炉位</h2>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>标签</th><th>备注</th><th>换档预热 min</th><th></th></tr></thead>
    <tbody>{rows.map(o => <tr key={o.id}><td>{o.label}</td><td>{o.capacity_note}</td>
      <td><input className="mono" type="number" min={0} style={{ width: 90 }}
        value={draft[o.id] ?? o.preheat_min}
        onChange={e => setDraft(d => ({ ...d, [o.id]: Number(e.target.value) }))} /></td>
      <td><button onClick={() => save(o)}>保存</button></td></tr>)}</tbody></table>
  </>);
}
