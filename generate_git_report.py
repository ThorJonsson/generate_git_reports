import argparse
import datetime as dt
import subprocess
import calendar
import time
from dateutil import rrule
from glob import glob

def weeks_between(start_date, end_date):
    weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=end_date)
    return weeks.count()

def format_date(date):
    return date.strftime('%m/%d/%Y')

def to_datetime(date, format_='%m/%d/%Y'):
    return dt.datetime.strptime(date, format_)

def increment(date, interval=7):
    try:
        return date + dt.timedelta(days=interval)
    except TypeError:
        date = to_datetime(date)
        return date + dt.timedelta(days=interval)

def create_txt(since, until, name, last_commit=None, debug=False):
    
    #CREATE SUMMARY
    cmd = f'git log --since {since} --until {until} '
    cmd += f'--no-merges --oneline --decorate > '
    cmd += f'git_diffs/{name}_summary.txt'
    if debug:
        print(cmd)
    else:
        subprocess.call(cmd, shell=True)
    
    #PARSE COMMITS
    with open(f'git_diffs/{name}_summary.txt', 'r') as f:
        
        #I THINK THIS IS READING COMMITS IN TOP TO BOTTOM
        #WE NEED TO REVERSE THIS
        commits=f.readlines()
        commits=list(reversed(commits))

        #COMPARE OLDEST COMMIT FROM PREV WEEK
        #TO ELDEST COMMIT FROM CURR WEEK
        if last_commit != None and len(commits)!=0:
            eldest_commit = commits[0].split(' ')[0]
            cmd = f'git diff {last_commit} '
            cmd += f'{eldest_commit} '
            cmd += '*.py '
            cmd += f'> git_diffs/{name}_{last_commit}_{eldest_commit}.diff'
            if debug:
                print(cmd)
            else:
                subprocess.call(cmd, shell=True)
       

        #COMPARE EACH COMMIT SUCCESSIVELY
        if len(commits) != 0:
            for i in range(len(commits)):
                try:
                    curr_commit_hash=commits[i].split(' ')[0]
                    next_commit_hash=commits[i+1].split(' ')[0]
                    cmd = f'git diff {curr_commit_hash} '
                    cmd += f'{next_commit_hash} '
                    cmd += '*.py '
                    cmd += f'> git_diffs/{name}_{curr_commit_hash}_{next_commit_hash}.diff'
                    if debug:
                        print(cmd)
                    else:
                        subprocess.call(cmd, shell=True)
                except IndexError:
                    pass
            
            #RETURN OLDEST COMMIT FOR NEXT WEEK
            return commits[-1].split(' ')[0]
        
        else:
            return last_commit
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date')
    parser.add_argument('--end_date')
    parser.add_argument('--branch')
    args = parser.parse_args()
    subprocess.call(f'git checkout {args.branch}', shell=True)
    weeks = weeks_between(to_datetime(args.start_date), 
                        to_datetime(args.end_date))
    
    last_commit=None
    start_week = to_datetime(args.start_date)
    end_week = increment(start_week, 7)
    for _ in range(weeks):
        start_week = format_date(start_week)
        end_week = format_date(end_week)
        last_commit = create_txt(start_week, 
                                 end_week, 
                                 name=start_week.replace('/', '_'),
                                 last_commit=last_commit)
        start_week = increment(start_week, 7)
        end_week = increment(end_week, 7)
    
    diffs = sorted(glob('git_diffs/*.diff'))
    months=[]
    prev_day_int=1
    i=0
    for curr_iter, diff in enumerate(diffs):
        month_int=int(diff.split('_')[1].split('/')[1])
        curr_day_int=int(diff.split('_')[2])
        curr_year=diff.split('_')[3]
        month_name=calendar.month_name[month_int]
        if month_name not in months:
            if i != 0:
                tex+='\n'
                tex+=f'{chr(92)}'
                tex+='end{document}\n'
                with open(f'tex_reports/{args.branch}_{curr_year}_{months[-1]}.tex', 'w') as f:
                    for i in range(len(tex)):
                        f.write(tex[i])
                del tex
            tex='\documentclass{article}\n'
            tex+=r'\usepackage{minted}'
            tex+='\n'
            tex+=f'{chr(92)}'
            tex+='begin{document}\n'
            tex+='\t'
            tex+=f'{chr(92)}'
            tex+='section'
            tex+='{'
            tex+=f'{month_name}'
            tex+='}'
            tex+='\n'
            months.append(month_name)
            i=1
        if curr_day_int != prev_day_int:
            tex+='\t\t'
            tex+=f'{chr(92)}'
            tex+='subsection'
            tex+='{'
            tex+=f'Week {i}'
            tex+='}'
            tex+='\n'
            i+=1
        tex+='\t\t\t'
        tex+=f'{chr(92)}'
        tex+='inputminted[breaklines]{diff}{'
        tex+=f'{diff}'
        tex+='}\n'
        prev_day_int = curr_day_int
        
        if curr_iter == len(diffs):
            tex+='\n'
            tex+=f'{chr(92)}'
            tex+='end{document}\n'
            with open(f'tex_reports/{args.branch}_{curr_year}_{month_name}.tex', 'w') as f:
                for i in range(len(tex)):
                    f.write(tex[i])
