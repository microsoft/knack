Prompting
=========

We provide some utilities for prompting during command execution.

Use this sparingly and provide non-interactive ways to specify such arguments.

Each of these utility methods does a TTY check and raises a `NoTTYException`.
Handle this appropriately in each case.

Examples
--------

**A basic message prompt**

```Python
from knack.prompting import prompt
```

Prompt for any user input.

```Python
>>> username = prompt('What is your name? ')
What is your name? Jonathon
>>> username
'Jonathon'
```

If you provide a help string, the user can type '?' to request this help string. All the prompting types support this functionality.

```Python
>>> username = prompt('What is your name? ', help_string='The name you prefer to be known by.')
What is your name? ?
The name you prefer to be known by.
What is your name? Jon
>>> username
'Jon'
```

**Integer based prompt**

```Python
from knack.prompting import prompt_int
```

It's straightforward to get the number entered.

```Python
>>> number = prompt_int('How many do you want to create? ')
How many do you want to create? 10
>>> number
10
```

It has built-in checks that the user has entered an integer.

```Python
>>> number = prompt_int('How many do you want to create? ')
How many do you want to create? hello
hello is not a valid number
How many do you want to create?
 is not a valid number
How many do you want to create? ten
ten is not a valid number
How many do you want to create? 10
>>> number
10
```

**Password prompts**

```Python
from knack.prompting import prompt_pass
```

This is a simple password prompt. As you can see, the entered password is not printed to the screen but is saved in the variable.

```Python
>>> userpassword = prompt_pass()
Password:
>>> userpassword
'password123!@#'
```

You can change the prompt message with the `msg` argument.

```Python
>>> secret = prompt_pass(msg='Client secret: ')
Client secret:
>>> secret
'm#@$%453edf'
```

If you're requesting a new password from the user, use the `confirm` argument.

```Python
>>> userpassword = prompt_pass(msg='New resource password: ', confirm=True)
New resource password:
Confirm New resource password:
>>> userpassword
'mysimplepassword'
```

If the passwords don't, the user will get a warning message and be required to enter again.

```Python
>>> userpassword = prompt_pass(msg='New resource password: ', confirm=True)
New resource password:
Confirm New resource password:
Passwords do not match.
New resource password:
```

**Boolean prompts**

```Python
from knack.prompting import prompt_y_n
```

```Python
>>> response = prompt_y_n('Do you agree to this? ')
Do you agree to this?  (y/n): y
>>> response
True
```

```Python
>>> response = prompt_y_n('Do you agree to this? ')
Do you agree to this?  (y/n): n
>>> response
False
```

A default value can be provided if a user does not specify one.

```Python
>>> prompt_y_n('Do you agree to this? ', default='y')
Do you agree to this?  (Y/n):
True
```

We also have a similar prompt for True/False:
```Python
from knack.prompting import prompt_t_f
```

**Choice list prompts**

```Python
from knack.prompting import prompt_choice_list
```

Prompt the user to choose from a choice list.
You will be given the index of the list item the user selected.

```Python
>>> a_list = ['size A', 'size B', 'size C']
>>> choice_index = prompt_choice_list('Default output type? ', a_list)
Default output type?
 [1] size A
 [2] size B
 [3] size C
Please enter a choice [1]: 3
>>> choice_index
2
```

You can also provide a list with descriptions.


```Python
>>> a_list = [{'name':'size A', 'desc':'A smaller size'}, {'name':'size B', 'desc':'An average size'}, {'name':'size C', 'desc':'A bigger size'}]
>>> choice_index = prompt_choice_list('Default output type? ', a_list)
Default output type?
 [1] size A - A smaller size
 [2] size B - An average size
 [3] size C - A bigger size
Please enter a choice [1]: 2
```
