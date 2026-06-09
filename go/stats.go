package main

import (
	"fmt"
	"os"
	"time"
	"sort"
	"gopkg.in/src-d/go-git.v4"
	"gopkg.in/src-d/go-git.v4/plumbing/object"
)

const daysInLastSixMonths = 183
const outOfRange = 99999
const weeksInLastSixMonths = 26

type column []int



func stats(email string) {
    commits := processRepositories(email)
    printCommitsStats(commits)
}


func processRepositories(email string) map[int]int {
	filepath := getDotFilePath()
	repos := parseFileLinesToSlice(filepath )
	DaysInMap := daysInLastSixMonths
	commits :=make(map[int]int , DaysInMap)
	for i := DaysInMap; i > 0; i-- {
		commits[i] = 0
	}
	for _, path := range repos {
		commits = FillCommits(commits, path, email)
	}
	return commits
}



func FillCommits(commits map[int]int, path string, email string) map[int]int {
	repo, err := git.PlainOpen(path)
	if err != nil {
		panic(err)
	}
	ref, err := repo.Head()
	if err != nil {
		panic(err)
	}
	iter, err := repo.Log(&git.LogOptions{From: ref.Hash()})
	if err != nil {
		panic(err)
	}
	offset := CalcOffset()
	err = iter.ForEach(func(c *object.Commit) error {
		daysago := countDaysSinceDate(c.Author.When) + offset
		if c.Author.Email != email {
			return nil
		}
		if daysago != outOfRange {
			commits[daysago]++
		}
		return nil
	})
	if err != nil {
		panic(err)
	}
	return commits
}


func getBeginingOfDay(t time.Time) time.Time {
	y, m, d := t.Date()
	startOfDay := time.Date(y, m, d, 0, 0, 0, 0, t.Location())
	return startOfDay
}


func countDaysSinceDate(t time.Time) int {
	days := 0
	now := getBeginingOfDay(time.Now())
	for t.Before(now) {

		t = t.AddDate(0, 0, 1)
		days++
		if days > daysInLastSixMonths {
			return outOfRange
		}
	}
	return days
}

func CalcOffset() int {
	var offset int
	weekday := time.Now().Weekday()
	switch weekday {
	case time.Sunday:
		offset = 7
	case time.Monday:
		offset = 6
	case time.Tuesday:
		offset = 5
	case time.Wednesday:
		offset = 4
	case time.Thursday:
		offset = 3
	case time.Friday:
		offset = 2
	case time.Saturday:
		offset = 1
	}
	return offset
}
func printCommitsStats(commits map[int]int) {
    keys := sortMapIntoSlice(commits)
    cols := buildCols(keys, commits)
    printCells(cols)
}

func sortMapIntoSlice(m map[int]int) []int {
    var keys []int
    for k := range m {
        keys = append(keys, k)
    }
    sort.Ints(keys)
    return keys
}

func buildCols(keys []int, m map[int]int) map[int]column {
    cols := make(map[int]column)
    col := column{}
    for _, k := range keys {
        week := int(k / 7)
        day := int(k % 7)
        if day == 0 {
            col = column{}
        }
        col = append(col, m[k])
        if day == 6 {
            cols[week] = col
        }
    }
    return cols
}


func printCells(cols map[int]column) {
    for i := weeksInLastSixMonths; i >= 0; i-- {
        if col, ok := cols[i]; ok {
            for _, day := range col {
                printCell(day, false)
            }
            fmt.Println()
        }
    }
}

func printCell(val int, today bool) {
    escape := "\033[0;37;30m"
    switch {
    case val > 0 && val < 5:
        escape = "\033[1;30;47m"
    case val >= 5 && val < 10:
        escape = "\033[1;30;43m"
    case val >= 10:
        escape = "\033[1;30;42m"
    }
    if today {
        escape = "\033[1;37;45m"
    }
    if val == 0 {
        fmt.Fprintf(os.Stdout, "%s  - \033[0m", escape)
        return
    }
    str := "  %d "
    switch {
    case val >= 10:
        str = " %d "
    case val >= 100:
        str = "%d "
    }
    fmt.Fprintf(os.Stdout, "%s"+str+"\033[0m", escape, val)
}
