#!/usr/local/bin/perl -w
#
use strict;
use warnings;
#
use CGI qw(:standard);
use FindBin qw($Bin);
use LWP::UserAgent;
use lib "$Bin";
#
# lyshie_20081022: global parameters
my $webmail    = '';
my $email      = '';
my $date_begin = '';
my $date_end   = '';
my $client_ip  = '';

my $ACCOUNT    = '';
my $HOST       = '';

sub getParams
{
    $date_begin = param('begin') || '1900-01-01';
    $date_begin =~ s/[^0-9\-]//g;

    $date_end = param('end') || '9999-12-31';
    $date_end =~ s/[^0-9\-]//g;

    $client_ip = $ENV{"HTTP_X_FORWARDED_FOR"}
                  || $ENV{"REMOTE_ADDR"}
                  || "";
}

sub getPortalCheck {
    my $sid = defined(param('sid')) ? param('sid') : '';
    $sid =~ s/[^0-9a-zA-Z]//g;

    my $ask_url = 'https://ua.net.nthu.edu.tw/portal/ask.cgi';

    if ($sid ne '') {
        my $ua = LWP::UserAgent->new();
        $ua->timeout(5);

        my $response;
        $response = $ua->get("$ask_url?sid=$sid");

        if ( $response->is_success() ) {
            my $ret = $response->content();

            my %hash = ();
            foreach (split(/[\n\r]+/, $ret)) {
                my ($key, $value);
                ($key, $value) = split(/\s*=\s*/, $_);
                $hash{$key} = $value;
            }

            if ($hash{'status'} eq 'ok') {
                $ACCOUNT = $hash{'uid'};
                $HOST    = $hash{'realm'};
                return \%hash;
            }
            else {
                return undef;
            }
        }
        else {
            return undef;
        }
    }
    else {
        return undef;
    }
}

sub main
{
    getParams();

    my $hash;
    unless ($hash = getPortalCheck())
    {
        my $back = $ENV{"HTTP_REFERER"} || "index.cgi";
        print header(-charset => 'utf-8');
        print <<EOF
<html>
<head>
<title>寄信紀錄查詢系統 (SMTP Query System)</title>
</head>
<body>
<pre>
Portal 驗證失敗，<a href="$back">回上一頁</a>。
</pre>
</body>
</html>
EOF
;
        exit();
    }


    $email = $ACCOUNT . '@' . $HOST;
    $email =~ m/@(.*)\.nthu\.edu\.tw$/;
    if (defined($1) && ($1 ne '')) {
        $webmail = "http://webmail.$1.nthu.edu.tw";
    }
    else {
        my $back = $ENV{"HTTP_REFERER"} || "index.cgi";
        print header(-charset => 'utf-8');
        print <<EOF
<html>
<head>
<title>寄信紀錄查詢系統 (SMTP Query System)</title>
</head>
<body>
<pre>
僅接受本校信箱查詢使用(即 .nthu.edu.tw 結尾)，<a href="$back">回上一頁</a>。
</pre>
</body>
</html>
EOF
;
        exit();
    }


    my $pid = 0;

    $pid = fork();

    if ($pid == 0) {
        my $cmd = sprintf("%s \"email=%s\" \"begin=%s\" \"end=%s\" \"client_ip=%s\" %s"
                             , "$Bin/smtplog.cgi"
                             , $email
                             , $date_begin
                             , $date_end
                             , $client_ip
                             , "< /dev/null > /dev/null 2>&1 &"
                         );
        exec($cmd);
    }
    else {
        print header(-charset => 'utf-8');
        print <<EOF
<html>
<head>
<title>寄信紀錄查詢系統 (SMTP Query System)</title>
</head>
<body>
<pre>
查詢紀錄已經寄出至 $email，寄達時間依信件大小而定。<br />
過大的信件，系統將打包成 ZIP 壓縮檔案。
</pre>
</body>
</html>
EOF
;
    }
}

main();
