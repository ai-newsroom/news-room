{
  lines[NR] = $0
}

END {
  last = NR
  while (last > 0 && lines[last] ~ /^[[:space:]]*$/) {
    last--
  }
  for (line = 1; line <= last; line++) {
    print lines[line]
  }
}
