# MIPS Prettifier Preprocessor and Documenter

An opinionated, but flexible, formatter and preprocessor for MIPS Assembly.

## tl;dr
Using all available features,
```shell
$ python3 mips.py input.s -o output.s --prettify -i -s -l -d
```

## Prettify
When using the prettify parameter,
a few formatting rules are applied throughout your code,
 - whitespace is normalised
 - instruction parameters are aligned
 - comments are aligned

Tabs are used for both indentation and alignment in the prettified/intermediate output,
which is aligned for editing in Visual Studio Code.
Spaces are used in the final/preprocessed code, so that your code looks consistent across different editors.

The output filename will be suffixed with `.pretty`.
When the `--replace` parameter is specified,
a backup of your file will be produced and the output replaces your input file.
A summary of the changes will also be printed to stdout.

## Preprocessor
All code written below a function label, until either the next function label or the end of the file,
will be considered as a single function.
By default, only the function named main will be transformed.
Use the `--add-function` argument to add additional function labels to be processed.


Variable placeholders, such as `%variableName`, in your assembly code are automatically replaced with registers.
During the replacement, temporary registers are preferred;
saved registers are only used when all temporary registers have been exhausted.
Append the `.s` flag to the end of your variable name to force usage of a saved register, `%variableName.s`.

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
A list of variables and their respective registers will be output to stdout for your reference.
This flag has no impact on the contents of the files output.


## Documentation Generation
Function documentation will be generated for you when the `--docs` parameter is specified.
The resulting documentation is only written to the output file, and is not included in the prettified file.
To save time from jumping back and forth between the source, prettified, and final versions,
the documentation is also printed to stdout.

### Frame and clobbers
Documentation for registers can be very useful, especially when
you need to save your registers on the stack.
It would be nice to know which variables are being clobbered,
so that you can store them in your function prologues.
This function documentation will be output for the previously used example function
```asm
#########################
# count

# Frame:      $ra, $s0
# Uses:       $s0, $t0
# Clobbers:   $t0
```

### Locals
Assembly would be so much easier to read if you knew what variables each register corresponds to.
Using the `--locals` argument will include the following comment in the output
```asm
# Locals:
#       - 'max' in $s0
#       - 'i' in $t0
```
This is especially useful if you want to debug the preprocessor,
and need to know exactly what it's doing with your beloved placeholder variables. 

### Structure
The flow of your program can be easily identified when you include structure documentation.
Note that you will have to manually indent and style the output.
```asm
# Structure:
#       - count_i_init
#       - count_i_cond
#       - count_i_step
#       - count_i_break
```

### Editing documentation
Comments written immediately above function labels will be output above the associated function documentation.
Should you wish to make any edits to the generated documentation,
make note of them or manually create a backup,
since any changes to the automatically generated function documentation *will be overridden*.
Remember to restore your finishing touches and edits before submitting your work.

## Version Control
It is completely up to you how to manage generated files with your version control system.
Since this tool makes back-ups of your code and generates multiple output files,
depending on your supplied parameters, here is an example to ignore all generated files
```gitignore
### Mips Preprocessor
# Backups
*.bak
# Prettified code
*.pretty.s
# Final output
*.out.s
```


## License
Made by David Wu and Eric Holmstrom.
&copy; 2020 All Rights Reserved.
See LICENSE for further details. 
