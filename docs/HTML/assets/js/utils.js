export const qs = (name, url = window.location.href) => new URL(url).searchParams.get(name);
export const el = (sel, root=document) => root.querySelector(sel);