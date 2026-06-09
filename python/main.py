import os
from datetime import datetime, timezone
import subprocess



DAYS = 183
OUT_OF_RANGE = 99999
WEEKS = 26
class RepoStore:
    def __init__(self, path="~/.gogitlocalstats"):
        self.path = path
    def read(self) -> list[str]:
        with open(self.path) as f:
            return [line.strip() for line in f.readlines()]

    def write(self, repos: list[str]):
        with open(self.path, "w") as f:
            for r in repos:
                f.write(r + "\n")

    def merge(self, new_repos: list[str]) -> list[str]:
        existing = self.read()
        for r in new_repos:
            if r not in existing:
                existing.append(r)
        self.write(existing)
        return existing


class Scanner:
    @staticmethod
    def scan(root: str) -> list[str]:
        return Scanner._scan([], root)

    @staticmethod
    def _scan(folders, folder):
        folder = folder.rstrip("/")
        try:
            entries = os.scandir(folder)
        except PermissionError:
            return folders

        for entry in entries:
            if entry.is_dir():
                path = f"{folder}/{entry.name}"
                if entry.name == ".git":
                    print(path)
                    folders.append(path.removesuffix("/.git"))
                    continue
                if entry.name in ("vendor", "node_modules"):
                    continue
                folders = Scanner._scan(folders, path)
        entries.close()
        return folders

def get_begening_of_day(t: datetime)-> datetime:
    return datetime(t.year,t.month,t.day,tzinfo=t.tzinfo)

def calc_offset()->int:
    weekday = datetime.now().weekday()
    d={0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
    return d[weekday]

def count_days_since_date(t:datetime)->int:
    now = get_begening_of_day(datetime.now(tz=t.tzinfo))
    delta = now-t
    days=delta.days
    if delta.seconds>0 or delta.microseconds>0:
        days +=1
    if days > DAYS:
        return OUT_OF_RANGE
    return days

class GitLogFetcher:
    @staticmethod
    def fetch(repo_path: str) -> list[tuple[datetime, str]]:
        entries=[]
        results= subprocess.run(["git", "log","--all","--format=%at %ae"],
                                capture_output=True,text=True, cwd=repo_path
                                )
        if results.returncode != 0:
            return []
        for line in results.stdout.strip().split("\n"):
            if not line:
                continue
            ts, email = line.split(" ", 1)
            dt = datetime.fromtimestamp(int(ts),tz=timezone.utc)
            entries.append((dt, email))
        return entries

class ContribGrid():
    def __init__(self,email:str):
        self.email = email
        self.commits={}
        for i in range(1, DAYS + 1):
            self.commits[i]=0

    def build(self, repos:list):
        for repo in repos:
            entries = GitLogFetcher.fetch(repo)
            for dt, email in entries:
                if email != self.email:
                    continue
                days_ago=count_days_since_date(dt) + calc_offset()
                if days_ago == OUT_OF_RANGE:
                    continue
                self.commits[days_ago]+=1
        return self


class GridRenderer():
    @staticmethod
    def render(commits:dict[int,int]):
        keys = sorted(commits)
        cols= GridRenderer._build_cols(keys, commits)
        for week in range(WEEKS,-1,-1):
            if week in cols:
                for val in cols[week]:
                    GridRenderer._cell(val)
                print()

    @staticmethod
    def _build_cols(keys, commits):
        cols={}
        col=[]
        for k in keys:
            week= k // 7
            day = k % 7
            if day == 0:
                col = []
            col.append(commits[k])
            if day == 6:
                cols[week] = col
        return cols

    @staticmethod
    def _cell(val, today=False):
        if val == 0:
            print(f"\033[0;37;30m  - \033[0m", end="")
            return
        if today:
            escape = "\033[1;37;45m"
        elif val < 5:
            escape = "\033[1;30;47m"
        elif val < 10:
            escape = "\033[1;30;43m"
        else:
            escape = "\033[1;30;42m"
        if val >= 100:
            fmt = f"{escape}{val} \033[0m"
        elif val >= 10:
            fmt = f"{escape} {val} \033[0m"
        else:
            fmt = f"{escape}  {val} \033[0m"
        print(fmt, end="")


class GitAnalyzer:
    def __init__(self, store_path="~/.gogitlocalstats"):
        self.store = RepoStore(store_path)

    def run(self, scan_path: str, email: str | None = None):
        repos = Scanner.scan(scan_path)
        self.store.merge(repos)
        if email:
            grid = ContribGrid(email).build(self.store.read())
            GridRenderer.render(grid.commits)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py <directory> [email]")
        sys.exit(1)
    analyzer = GitAnalyzer()
    analyzer.run(sys.argv[1], sys.argv[2] if len(sys.argv) >= 3 else None)
