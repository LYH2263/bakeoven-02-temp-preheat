import { useEffect, useState } from "react";
import { api } from "../api/client";
type P = { id: number; name: string; ferment_min: number; bake_min: number; temp_tier: string };
const TIERS = ["低温", "中温", "高温"];
export default function ProductsPage() {
  const [rows, setRows] = useState<P[]>([]);
  const [draft, setDraft] = useState<Record<number, string>>({});
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => {
    api<P[]>("/products").then(rs => {
      setRows(rs);
      setDraft(Object.fromEntries(rs.map(p => [p.id, p.temp_tier])));
    });
  }, []);
  async function save(p: P) {
    setMsg(""); setErr("");
    try {
      const v = (draft[p.id] ?? p.temp_tier).trim();
      if (!v) { setErr("温度档不能为空"); return; }
      const u = await api<P>(`/products/${p.id}`, { method: "PATCH", body: JSON.stringify({ temp_tier: v }) });
      setRows(rs => rs.map(r => (r.id === p.id ? u : r)));
      setDraft(d => ({ ...d, [p.id]: u.temp_tier }));
      setMsg(`已保存 ${p.name}：温度档 ${u.temp_tier}`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>产品（配方时长与温度档）</h2>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>名称</th><th>发酵 min</th><th>烘烤 min</th><th>合计</th><th>温度档</th><th></th></tr></thead>
    <tbody>{rows.map(p => <tr key={p.id}><td>{p.name}</td><td className="mono">{p.ferment_min}</td><td className="mono">{p.bake_min}</td><td className="mono">{p.ferment_min + p.bake_min}</td>
      <td><input list="temp-tiers" style={{ width: 90 }}
        value={draft[p.id] ?? p.temp_tier}
        onChange={e => setDraft(d => ({ ...d, [p.id]: e.target.value }))} /></td>
      <td><button onClick={() => save(p)}>保存</button></td></tr>)}</tbody></table>
    <datalist id="temp-tiers">{TIERS.map(t => <option key={t} value={t} />)}</datalist>
  </>);
}
