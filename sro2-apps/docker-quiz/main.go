// Docker Quiz — консольная викторина по Docker и Linux.
// Вопросы лежат в questions.json и вшиваются в бинарник через go:embed,
// поэтому финальный образ собирается FROM scratch и весит пару мегабайт.
package main

import (
	"bufio"
	_ "embed"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"strings"
	"time"
)

//go:embed questions.json
var questionsJSON []byte

type Question struct {
	Text    string   `json:"q"`
	Options []string `json:"options"`
	Answer  int      `json:"answer"` // индекс правильного варианта, с 0
	Why     string   `json:"why"`
}

const (
	bold  = "\033[1m"
	green = "\033[32m"
	red   = "\033[31m"
	cyan  = "\033[36m"
	reset = "\033[0m"
)

func main() {
	count := flag.Int("n", 10, "сколько вопросов задать")
	list := flag.Bool("list", false, "показать все вопросы с ответами и выйти")
	flag.Parse()

	var questions []Question
	if err := json.Unmarshal(questionsJSON, &questions); err != nil {
		fmt.Println("ошибка в questions.json:", err)
		os.Exit(1)
	}

	if *list {
		for i, q := range questions {
			fmt.Printf("%2d. %s\n    → %s\n", i+1, q.Text, q.Options[q.Answer])
		}
		return
	}

	rng := rand.New(rand.NewSource(time.Now().UnixNano()))
	rng.Shuffle(len(questions), func(i, j int) { questions[i], questions[j] = questions[j], questions[i] })
	if *count < 1 || *count > len(questions) {
		*count = len(questions)
	}
	questions = questions[:*count]

	fmt.Printf("%s%s\n  DOCKER QUIZ · вопросов: %d\n  Отвечайте цифрой 1-4, q — выход%s\n", cyan, bold, len(questions), reset)

	in := bufio.NewScanner(os.Stdin)
	score, answered := 0, 0
	start := time.Now()

quiz:
	for i, q := range questions {
		fmt.Printf("\n%s[%d/%d] %s%s\n", bold, i+1, len(questions), q.Text, reset)
		for j, opt := range q.Options {
			fmt.Printf("   %d) %s\n", j+1, opt)
		}

		pick := ask(in, len(q.Options))
		if pick == 0 {
			break quiz
		}
		answered++

		if pick-1 == q.Answer {
			score++
			fmt.Printf("  %s✔ верно%s\n", green, reset)
		} else {
			fmt.Printf("  %s✘ неверно%s, правильно: %s\n", red, reset, q.Options[q.Answer])
		}
		fmt.Printf("  %s\n", q.Why)
	}

	if answered == 0 {
		fmt.Println("\nНи одного ответа — до встречи!")
		return
	}
	total := answered
	fmt.Printf("\n%s══════════════════════════════%s\n", cyan, reset)
	fmt.Printf("  Результат: %s%d из %d%s за %s\n", bold, score, total, reset, time.Since(start).Round(time.Second))
	fmt.Printf("  %s\n", verdict(score, total))
}

// ask читает номер варианта от 1 до max; 0 — пользователь ввёл q.
func ask(in *bufio.Scanner, max int) int {
	for {
		fmt.Print("  > ")
		if !in.Scan() {
			fmt.Println("\n\nНет ввода. Запустите с флагом -it:  docker run --rm -it <образ>")
			os.Exit(1)
		}
		s := strings.TrimSpace(in.Text())
		if s == "q" {
			return 0
		}
		var pick int
		if n, err := fmt.Sscanf(s, "%d", &pick); n == 1 && err == nil && pick >= 1 && pick <= max {
			return pick
		}
		fmt.Println("  введите номер варианта")
	}
}

func verdict(score, total int) string {
	p := score * 100 / total
	switch {
	case p == 100:
		return "Идеально — можно идти в DevOps."
	case p >= 70:
		return "Хорошо, основы Docker понятны."
	case p >= 40:
		return "Неплохо, но стоит перечитать docker --help."
	default:
		return "Пора открыть документацию Docker."
	}
}
