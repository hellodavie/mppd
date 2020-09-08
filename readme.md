# MIPS Prettifier Preprocessor and Documenter

Using all available features,
```shell
python mips.py --prettify --replace --identifiers --locals --docs YOUR_INPUT_FILE.s
```

## Prettify
Whitespace is normalised when using the prettify parameter.
Instruction parameters and comments will be realigned throughout your code.
Tabs are used for both indentation and alignment in the prettified/intermediate output,
which is aligned for editing in Visual Studio Code.
Spaces are used in the final/preprocessed code, so that your code looks consistent across different editors.

## Preprocessor
All code written below a function label, until either the next function label or the end of the file,
will be considered as a single function.
By default, only the function named main will be transformed.
Use the `--add-function` argument to add additional function labels to be processed.


Variable placeholders `%variableName` in your assembly code are automatically replaced with registers.
Temporary registers are preferred;
saved registers are only used when there are no temporary registers remaining.
Append the `.s` flag at the end of your variable name to force usage of a saved register, `%variableName.s`

Consider the following assembly code,
```asm
count:
    li      %max.s, 10                  # int max = 10;
count_i_init:
    li      %i, 0                       # int i = 0;
count_i_cond:
    bge     %i, %max, count_i_break     # for (i < max)
    # ...
count_i_step:
    addi    %i, %i, 1                   # i++;
count_i_break:
    jr      $ra                         # return;
```

Using the command,
```shell
$ mppd count.s --prettify --add-function count
```

we get the following output,
```asm
count:
    li      $s0, 10                     # int max = 10;
count_i_init:
    li      $t0, 0                      # int i = 0;
count_i_cond:
    bge     $t0, $s0, count_i_break     # for (i < max)
    # ...
count_i_step:
    addi    $t0, $t0, 1                 # i++;
count_i_break:
    jr      $ra                         # return;
```

Notice that one of the variables has a flag which forces the usage of a saved register in the output code,
rather than a temporary register.

The `--identifiers` parameter will output preprocessor information for each function processed.
A list of variables and their respective registers will be output for your reference.


## Documentation Generation
Function documentation will be generated for you when the `--docs` parameter is specified.

#### Frame and clobbers
Documentation for registers can be very useful, especially when
you need to save your registers on the stack.
It would be nice to know which variables are being clobbered.
Using the frame and clobbers 

## License
Made by David Wu and Eric Holmstrom.
&copy; 2020 All Rights Reserved.
See LICENSE for further details. 
