#!/usr/local/bin/perl -w
#
use strict;
use warnings;
#
use FindBin qw($Bin);
use lib "$Bin";
use CGI qw(:standard);
#
if (defined($ENV{"HTTP_X_FORWARDED_FOR"})
    || defined($ENV{"REMOTE_ADDR"})
   ) {
    print header(-charset => 'utf-8');
    print <<EOF
<html>
<head>
<title>寄信紀錄查詢系統 (SMTP Query System)</title>
</head>
<body>
<pre>
禁止執行！
</pre>
</body>
</html>
EOF
;
    exit(1);
}
#
# lyshie_20081022: global configs
my $SMTPLOG_PATH = "/logpool/mail_from";
my $SMTPLOG_NOTIFIER = "$Bin/smtplog.cgi";
#

my @users = ();
my $today = "";
my $threshold = 200;
my @tops = ();
my $count = 0;
#my @ignores = ('@list.(net|oz).nthu.edu.tw$',
               #'@(my).nthu.edu.tw$'
#              );
my @ignores = ();

sub getToday
{
    my @date = '';
    @date = localtime(time() - 86400);
    return sprintf("%04d-%02d-%02d", $date[5] + 1900
                                   , $date[4] + 1
                                   , $date[3]
                  );
}

sub getUsers
{
    my $date = shift;
    my @all = ();

    unless (-d "$SMTPLOG_PATH/$date") {
        print("Error: Invalid date format.\n");
        exit(1);
    }

    opendir(DH, "$SMTPLOG_PATH/$date");
    @all = grep { -f "$SMTPLOG_PATH/$date/$_" & m/nthu\.edu\.tw$/ }
                readdir(DH);
    closedir(DH);

    return @all;
}

sub getSummary
{
    my $date = shift;
    my $user = shift;
    my $file = "$SMTPLOG_PATH/$date/$user";

    my %rows = ();
    my @keys = ();
    my @values = ();
    my $buf = "";
    my $buf2 = "";

    open(FH, $file);
        $buf = <FH>;
        chomp($buf);
        $buf =~ s/^#\s//g;
        $buf2 = <FH>;
        chomp($buf2);
        $buf2 =~ s/^#\s//g;
    close(FH);


    @keys   = map { $_ =~ s/^\s+//g;
                    $_ =~ s/\s+$//g;
                    $_;
                  } map { lc($_) } split(/\|/, $buf);
    @values = map { $_ =~ s/^\s+//g;
                    $_ =~ s/\s+$//g;
                    $_;
                  } split(/\|/, $buf2);

    foreach (my $i = 0; $i < @keys; $i++) {
        $rows{$keys[$i]} = $values[$i];
    }

    return %rows;
}

sub checkSMTP
{
    my $row = shift;

    if ($row->{'sum'} > $threshold) {
        foreach (@ignores) {
            if ($row->{'mail from'} =~ qr/$_/) {
                return;
            }
        }
        push(@tops, $row);
    }
}

sub showTops
{
    my $date = shift;

    @tops = sort { $b->{'sum'} <=> $a->{'sum'} } @tops;
    @tops = @tops[0..$count - 1] if ($count && $count < scalar(@tops));

    foreach my $t (@tops) {
        printf("%8d (%s)\n", $t->{'sum'}
                           , $t->{'mail from'}
              );
    }

    printf("Date:\t%s\nTotal:\t%d (Over %d)\n", $date
                                              , scalar(@tops)
                                              , $threshold
          );
}

sub notifyTops
{
    my $date = shift;

    foreach (@tops) {
        my $url = sprintf("%s \"threshold=250&email=%s&begin=%s&end=%s\" > /dev/null 2>&1"
                          , $SMTPLOG_NOTIFIER
                          , $_->{'mail from'}
                          , $date
                          , $date
                         );
        print $url, "\n"; 
        `$url`;
    }
}

sub main
{
    $count = $ARGV[1] || 0;
    $today = $ARGV[0] || getToday();
    @users = getUsers($today);

    foreach my $user (@users) {
        my %ref = getSummary($today, $user);
        checkSMTP(\%ref);
    }

    showTops($today);

    notifyTops($today);
}

main();
