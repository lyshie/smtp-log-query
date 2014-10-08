#!/usr/local/bin/perl -w
#
use strict;
use warnings;
#
use CGI qw(:standard);
use FindBin qw($Bin);
use lib "$Bin";
use ValidateCheck;
#
# lyshie_20081022: global parameters
my $webmail    = '';
my $email      = '';
my $code       = '';
my $date_begin = '';
my $date_end   = '';
my $client_ip  = "";

sub getParams
{
    $email = param('email') || '';
    $email =~ s/[^a-zA-Z0-9\.\-_@]//g;

    $code = param('code') || '';
    $code =~ s/[^0-9]//g;

    $date_begin = param('begin') || '1900-01-01';
    $date_begin =~ s/[^0-9\-]//g;

    $date_end = param('end') || '9999-12-31';
    $date_end =~ s/[^0-9\-]//g;

    $client_ip = $ENV{"HTTP_X_FORWARDED_FOR"}
                  || $ENV{"REMOTE_ADDR"}
                  || "";
}

sub main
{
    getParams();

    if (checkRemoteValidate(param('validate'), param('host')) == 0)
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
驗證碼錯誤，<a href="$back">回上一頁</a>。
</pre>
</body>
</html>
EOF
;
        exit();
    }


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
