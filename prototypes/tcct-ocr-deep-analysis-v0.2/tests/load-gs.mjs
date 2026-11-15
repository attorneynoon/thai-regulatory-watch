import fs from 'node:fs';
import vm from 'node:vm';

export function loadGsFiles(names) {
  const context = {
    console,
    JSON,
    Date,
    Math,
    RegExp,
    String,
    Number,
    Boolean,
    Array,
    Object,
    Set,
    Map,
  };
  context.globalThis = context;
  vm.createContext(context);

  for (const name of names) {
    const url = new URL(`../gas/${name}`, import.meta.url);
    const source = fs.readFileSync(url, 'utf8');
    vm.runInContext(source, context, { filename: name });
  }
  return context;
}
