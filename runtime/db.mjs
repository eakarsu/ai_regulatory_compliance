import { spawnSync } from 'node:child_process';

export function literal(value){return "'" + String(value).replaceAll("'", "''") + "'";}
export function query(sql,{rows=false}={}){
  const args=[process.env.DATABASE_URL,'-v','ON_ERROR_STOP=1'];
  if(rows)args.push('-At','-F','\t');
  args.push('-c',sql);
  const result=spawnSync('psql',args,{encoding:'utf8'});
  if(result.status!==0)throw new Error((result.stderr||result.stdout||'database request failed').trim());
  return result.stdout.trim();
}
export function executeScript(sql){
  const result=spawnSync('psql',[process.env.DATABASE_URL,'-v','ON_ERROR_STOP=1','-f','-'],{encoding:'utf8',input:sql});
  if(result.status!==0)throw new Error((result.stderr||result.stdout||'database setup failed').trim());
}

