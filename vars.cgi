#relative to script location or full server path if microsoft
$archivepath = "../../wordsearch";

#$baseurl = "http://www.somewhereincanada.com";
$baseurl = "";

#$archiveurl = "http://127.0.0.1/crosswords";
$archiveurl = "$baseurl/wordsearch";

$scripturl = "$baseurl/cgi/wordsearch";

$SEND_MAIL= "/usr/lib/sendmail -t";
#example: $SEND_MAIL="/usr/lib/sendmail -t";

#$SMTP_SERVER="mail.yourdomain.com";
#use SMTP_SERVER if SEND_MAIL is unavailable, BUT NOT BOTH
#example: $SMTP_SERVER="mail.yourdomain.com";

$from = "Word Search Mailer Ver 1.0 <vpelss\@emogic.com>";
#This will be in all Email from addresses
#example $from = "Tarot Mailer Ver 1.0 <vpelss\@emogic.com>";
#THE SLASH IS MANDITORY!

$subject = "Word Search from Emogic.com";
#email subject. Note: The script adds the visitors name will show at the end

#to wrap around the word $item on the template page
$preitemtoeval = '$preitem = "<a href=http://www.google.ca/search?q=$item target=_blank>"';
$postitem = "</a>";


# --------------------------------------------------------
#common routines. Do not modify.
# --------------------------------------------------------

sub parse_form {
# --------------------------------------------------------
# Parses the form input and returns a hash with all the name
# value pairs. Removes SSI and any field with "---" as a value
# (as this denotes an empty SELECT field.

        my (@pairs, %in);
        my ($buffer, $pair, $name, $value);

        if ($ENV{'REQUEST_METHOD'} eq 'GET') {
                @pairs = split(/&/, $ENV{'QUERY_STRING'});
        }
        elsif ($ENV{'REQUEST_METHOD'} eq 'POST') {
                read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
                 @pairs = split(/&/, $buffer);
        }
        else {
                &cgierr ("This script must be called from the Web\nusing either GET or POST requests\n\n");
        }
        PAIR: foreach $pair (@pairs) {
                ($name, $value) = split(/=/, $pair);

                $name =~ tr/+/ /;
                $name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

                $value =~ tr/+/ /;
                $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

                $value =~ s/<!--(.|\n)*-->//g;                          # Remove SSI.
                if ($value eq "---") { next PAIR; }                  # This is used as a default choice for select lists and is ignored.
                (exists $in{$name}) ?
                        ($in{$name} .= "~~$value") :              # If we have multiple select, then we tack on
                        ($in{$name}  = $value);                                  # using the ~~ as a seperator.
        }
        return %in;
}

##################################################################
sub valid_address
 {
  $testmail = $_[0];
  if ($testmail =~/ /)
   { return 0; }
  if ($testmail =~ /(@.*@)|(\.\.)|(@\.)|(\.@)|(^\.)/ ||
  $testmail !~ /^.+\@(\[?)[a-zA-Z0-9\-\.]+\.([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/)
   { return 0; }
   else { return 1; }
}

##################################################################
sub bad_email
{
print qq|

Content-type: text/html

<FONT SIZE="+1">
<B>
SORRY! Your request could not be processed because of an
improperly formatted e-mail address. Please use your browser's
back button to return to the form entry page.
</B>
</FONT>

|;
}

sub sendmail  {
# error codes below for those who bother to check result codes <gr>
# 1 success
# -1 $smtphost unknown
# -2 socket() failed
# -3 connect() failed
# -4 service not available
# -5 unspecified communication error
# -6 local user $to unknown on host $smtp
# -7 transmission of message failed
# -8 argument $to empty
#
#  Sample call:
#
# &sendmail($from, $reply, $to, $smtp, $subject, $message );
#
#  Note that there are several commands for cleaning up possible bad inputs - if you
#  are hard coding things from a library file, so of those are unnecesssary
#

    my ($fromaddr, $replyaddr, $to, $smtp, $subject, $message) = @_;

    $to =~ s/[ \t]+/, /g; # pack spaces and add comma
    $fromaddr =~ s/.*<([^\s]*?)>/$1/; # get from email address
    $replyaddr =~ s/.*<([^\s]*?)>/$1/; # get reply email address
    $replyaddr =~ s/^([^\s]+).*/$1/; # use first address
    $message =~ s/^\./\.\./gm; # handle . as first character
    $message =~ s/\r\n/\n/g; # handle line ending
    $message =~ s/\n/\r\n/g;
    $smtp =~ s/^\s+//g; # remove spaces around $smtp
    $smtp =~ s/\s+$//g;

    if (!$to)
    {
        return(-8);
    }

 if ($SMTP_SERVER ne "")
  {
    my($proto) = (getprotobyname('tcp'))[2];
    my($port) = (getservbyname('smtp', 'tcp'))[2];

    my($smtpaddr) = ($smtp =~
                     /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/)
        ? pack('C4',$1,$2,$3,$4)
            : (gethostbyname($smtp))[4];

    if (!defined($smtpaddr))
    {
        return(-1);
    }

    if (!socket(MAIL, AF_INET, SOCK_STREAM, $proto))
    {
        return(-2);
    }

    if (!connect(MAIL, pack('Sna4x8', AF_INET, $port, $smtpaddr)))
    {
        return(-3);
    }

    my($oldfh) = select(MAIL);
    $| = 1;
    select($oldfh);

    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-4);
    }

    print MAIL "helo $SMTP_SERVER\r\n";
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-5);
    }

    print MAIL "mail from: <$fromaddr>\r\n";
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-5);
    }

    foreach (split(/, /, $to))
    {
        print MAIL "rcpt to: <$_>\r\n";
        $_ = <MAIL>;
        if (/^[45]/)
        {
            close(MAIL);
            return(-6);
        }
    }

    print MAIL "data\r\n";
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close MAIL;
        return(-5);
    }

   }

  if ($SEND_MAIL ne "")
   {
     open (MAIL,"| $SEND_MAIL");
   }

    print MAIL "To: $to\n";
    print MAIL "From: $fromaddr\n";
    #print MAIL "Reply-to: $replyaddr\n" if $replyaddr;
    print MAIL "Subject: $subject\n";
    print MAIL 'Mime-Version: 1.0'."\n";
    print MAIL 'content-type:' . "text/HTML\n\n"; # <----------------- put the double \n\n here
    #print MAIL "Content-Transfer-Encoding: quoted-printable\n\n";

    print MAIL "$message";
    print MAIL "\n.\n";

 if ($SMTP_SERVER ne "")
  {
    $_ = <MAIL>;
    if (/^[45]/)
    {
        close(MAIL);
        return(-7);
    }

    print MAIL "quit\r\n";
    $_ = <MAIL>;
  }

    close(MAIL);
    return(1);
}

sub cgierr {
# --------------------------------------------------------
# Displays any errors and prints out FORM and ENVIRONMENT
# information. Useful for debugging.
#
    if (!$html_headers_printed) {
        print "Content-type: text/html\n\n";
        $html_headers_printed = 1;
    }
    print "<PRE>\n\nCGI ERROR\n==========================================\n";
    $_[0]      and print "Error Message       : $_[0]\n";
    $0         and print "Script Location     : $0\n";
    $]         and print "Perl Version        : $]\n";

    print "\nForm Variables\n-------------------------------------------\n";
    foreach $key (sort keys %in) {
        my $space = " " x (20 - length($key));
        print "$key$space: $in{$key}\n";
    }
=pod
    print "\nEnvironment Variables\n-------------------------------------------\n";
    foreach $env (sort keys %ENV) {
        my $space = " " x (20 - length($env));
        print "$env$space: $ENV{$env}\n";
    }
=cut
    print "\n</PRE>";
    exit -1;
}

1;