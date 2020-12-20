CC := g++-10
TARGET := solution

SRC := solution.c
OBJ := $(SRC:.c=.o)
DEP := $(OBJ:%.o=%.d)

UNAME := $(shell uname)
LOCAL := 0
DEBUG := 0
FLTO := 0


COMMONFLAGS := -Wall -Werror -Wextra -ffast-math
CFLAGS := $(COMMONFLAGS) #-std=c99 -g -flto
LDFLAGS := $(COMMONFLAGS) -lm -ldl -flto 

ifeq ($(DEBUG),1)
	CFLAGS += -O0 -DDEBUG
else
	CFLAGS += -O3 -DNDEBUG
endif

# CFLAGS += -march=x86-64

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) $^ -o $@

%.o: %.c Makefile
	$(CC) $(CFLAGS) -MMD -c $< -o $@

-include $(DEP)

.PHONY: default format clean print_local_warning
clean:
	rm -f *.o *.d* *~ $(TARGET)

format:
	clang-format -i --style=file *.c *.h