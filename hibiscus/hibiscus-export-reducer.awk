# call me like this:
# awk -f hibiscus-export-reducher.awk < hibiscus-export-example.csv

BEGIN { 
	FS=";";
    outcsv="";
    matched=0;
    total=0;
    year = strftime("%Y");
}

FNR == 1 {
    if ($0 != "\"#\";\"IBAN\";\"BIC\";\"Konto\";\"Gegenkonto\";\"Gegenkonto BLZ\";\"Gegenkonto Inhaber\";\"Betrag\";\"Valuta\";\"Datum\";\"Verwendungszweck\";\"Verwendungszweck 2\";\"Zwischensumme\";\"Primanota\";\"Kundenreferenz\";\"Kategorie\";\"Notiz\";\"Weitere Verwendungszwecke\";\"Art\";\"Vormerkbuchung\";\"End-to-End ID\"")
    {
        print "Warning: Hibiscus column scheme has changed. Please check if this little awk script still matches the right columns." > "/dev/stderr";
        print "" > "/dev/stderr";
    }
}

FNR > 1 {
    total = total + 1;
    reference = $11;  # 11=Verwendungszweck, 12=Verwendungszweck 2, 18=Weitere Verwendungszwecke
    if ($12 != "\"\"") reference = substr(reference, 0, length(reference)-1) " " substr($12, 1)
    if ($18 != "\"\"") reference = substr(reference, 0, length(reference)-1) " " substr($18, 1)
    #                            prefix  year                -code
    position = match(reference, /C3S-dues[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][^0-9]/);  # code expected to have exact four digits
    if (position > 0)  # && substr(reference, position+8, 4) == year)  <- uncomment, if you want to filter only payments of the current year
    {
        if (outcsv == "")
            outcsv = "\"Datum\";\"Gegenkonto Inhaber\";\"Verwendungszwecke\";\"Betrag\";\"Rechnungscode\"\n"

        outcsv = outcsv $10 ";" $7 ";" reference ";" $8 ";\"" substr(reference, position+8, 9) "\"" "\n";  # append matching code
        matched = matched + 1;
    }
    else
    {        
        print "Line not matched: " $0 > "/dev/stderr";
    }
}

END { 
    print "" > "/dev/stderr"
    print matched " of " total " lines matched." > "/dev/stderr"
    print "Codes are written to stdout..." > "/dev/stderr"
    print outcsv
}
