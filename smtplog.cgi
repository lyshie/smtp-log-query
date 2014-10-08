#!/usr/local/bin/perl -w
#
use strict;
use warnings;
#
use CGI qw(:standard);
use MIME::Lite;
use FindBin qw($Bin);
#
# lyshie_20081022: global configs
my $SMTPLOG_PATH = "/logpool/mail_from";
#
# lyshie_20081022: global parameters
my $email      = '';
my $date_begin = '';
my $date_end   = '';
my $count      = 0;
my $buffer     = '';
my $threshold  = 99999999;
my $client_ip = '127.0.0.1';

my %ARGVS = ();
my %TAGS = ( 'sum'      => '總和',
             'auth'     => '驗證寄信',
             'bounced'  => '退信',
             'deferred' => '延遲',
             'expired'  => '逾期',
             'sent'     => '成功寄出',
           );

sub getArgvs
{
    foreach my $a (@ARGV) {
        my ($k, $v) = split(/=/, $a, 2);
        $ARGVS{$k} = $v || '';
    }
}

sub getParams
{
    $email = param('email') || $ARGVS{'email'} || '';
    $email =~ s/[^a-zA-Z0-9\.\-_@]//g;

    $date_begin = param('begin') || $ARGVS{'begin'} || '1900-01-01';
    $date_begin =~ s/[^0-9\-]//g;

    $date_end = param('end') || $ARGVS{'end'} || '9999-12-31';
    $date_end =~ s/[^0-9\-]//g;

    $threshold    = param('threshold') || $ARGVS{'threshold'} || 99999999;
    $client_ip    = param('client_ip') || $ARGVS{'client_ip'} || '127.0.0.1';
}

sub getLogfile
{
    my $date = shift || return;
    my $logfile = "$SMTPLOG_PATH/$date/$email";
    return unless (-f $logfile);

    my ($sender_ip, $relay, $time, $msg_id, $status, $resp) = ();
    open(FH, $logfile);
    while (<FH>) {
        next if ($_ =~ m/^#/);
        chomp($_);
        my $line = $_;
        $line =~ s/^\s+//g;
        $line =~ s/\s+$//g; 
        ($sender_ip, $relay, $time, $msg_id, $status, $resp) =
                                                    ('', '', '', '', '', ''); 
        ($sender_ip, $relay, $time, $msg_id, $status, $resp) =
                                                    split(/\s+/, $line, 6);
        $sender_ip =~ s/[^0-9\.]//g;
        $count++;

        # lyshie_20081119: show the maximum 250 per day
        next if ($count > $threshold);

        my @froms = split(/\s+/, $resp, 3);
        $resp = join("<br />", @froms);

        $sender_ip = $sender_ip || '&nbsp;';

        $buffer .= <<EOF
	<tr>
		<td nowrap>$count</td>
		<td nowrap>$sender_ip</td>
		<td nowrap>$relay</td>
		<td nowrap>$date $time</td>
		<td nowrap>$msg_id</td>
		<td nowrap>$status</td>
		<td>$resp</td>
	</tr>
EOF
;
    }
    close(FH);
}

sub getSummary
{
    my %fields = ();
    my %data = ();

    $buffer .= <<EOF
<br />信件寄送統計
EOF
;
    opendir(DH, "$SMTPLOG_PATH");
    my @dirs = grep {-d "$SMTPLOG_PATH/$_" && m/^\d\d\d\d\-\d\d-\d\d$/ }
                   readdir(DH);
    closedir(DH);
    @dirs = sort(@dirs);

    my $total = 0;
    foreach my $dir (@dirs) {
        if (($dir ge $date_begin) && ($dir le $date_end)) {
            my $file = "$SMTPLOG_PATH/$dir/$email";
            unless (-f $file) {
                $data{$dir} = undef;
                next;
            }
            open(FH, $file);
                my $line  = <FH>;
                my $line2 = <FH>;
                chomp($line);
                chomp($line2);
                $line  =~ s/#\s+//g;
                $line2 =~ s/#\s+//g;
                my @f = split(/\|\s*/, $line);
                my @t = split(/\|\s*/, $line2);
                my %ref = ();
                for (my $i = 0; $i < scalar(@f); $i++) {
                    next if (lc($f[$i]) eq 'mail from');
                    $fields{lc($f[$i])} = scalar(keys(%fields)) + 1 unless
                        $fields{lc($f[$i])};
                    $ref{lc($f[$i])} = $t[$i];
                    $data{$dir} = \%ref;
                }
            close(FH);
            $total++;
        }
    }

    if ($total == 0) {
        $buffer .= <<EOF
<span class="alert">查無紀錄！</span><br />
EOF
;
        return;
    }

    $buffer .= <<EOF
<table class="stats" border="1">
<tr>
EOF
;

    $buffer .= '<td class="hed" nowrap>日期<br />Date</td>';
    $buffer .= '<td class="hed" nowrap>' .
         $TAGS{$_} . '<br />' . uc(substr($_, 0, 1)) . substr($_, 1) . '</td>'
                   foreach (sort {$fields{$a} <=> $fields{$b}} keys(%fields)); 

    $buffer .= '</tr>';

    foreach my $d (sort(keys(%data))) {
        $buffer .= "<tr><td nowrap>$d</td>";
        foreach my $f (sort {$fields{$a} <=> $fields{$b}} keys(%fields)) {
            $buffer .= '<td nowrap>';
            $buffer .= $data{$d}->{$f} ? $data{$d}->{$f} : 0;
            $buffer .= '</td>';
        }
        $buffer .= '</tr>';
    }

    $buffer .= '</table>';
}

sub html_header
{
    $buffer .= <<EOF
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<style>
	body {
		font-family: Verdana, Geneva, Arial, Helvetica, sans-serif;
		font-size: 12px;
	}

	table.stats
	{
		text-align: center;
		font-family: Verdana, Geneva, Arial, Helvetica, sans-serif;
		font-weight: normal;
		font-size: 11px;
		color: #fff;
		width: 280px;
		background-color: #666;
		border: 0px;
		border-collapse: collapse;
		border-spacing: 0px;
	}

	table.stats td
	{
		background-color: #CCC;
		color: #000;
		padding: 4px;
		text-align: center;
		border: 1px #fff solid;
	}

	table.stats td.hed
	{
		background-color: #666;
		color: #fff;
		padding: 4px;
		text-align: center;
		border-bottom: 2px #fff solid;
		font-size: 12px;
		font-weight: bold;
	}

	.alert
	{
		color: #ff0000;
	}
</style>
</head>
<body>
EOF
;

    if ($client_ip eq '127.0.0.1') {
        $buffer .= <<EOF
<span class="alert">
本信係由「寄信紀錄查詢系統」自動寄出，請勿直接回信<br />
通知結果僅供參考，如有疑問請聯絡本中心(<a href="http://net.nthu.edu.tw/2009/about:contact" target="_blank">http://net.nthu.edu.tw/2009/about:contact</a>)<br />
</span>
<br />
寄信紀錄查詢系統(SMTP Query System)：<a href="http://net.nthu.edu.tw/redirect/smtpquery.htm">http://net.nthu.edu.tw/redirect/smtpquery.htm</a>
<br />
信箱(Email)：$email<br />
時間(Date)：$date_begin 至 $date_end 的寄信紀錄<br />
查詢來源(Client IP)：$client_ip<br />
EOF
;
    }
    else {
        $buffer .= <<EOF
<span class="alert">
本信係由「寄信紀錄查詢系統」自動寄出，請勿直接回信<br />
查詢結果僅供參考，如有疑問請聯絡本中心(<a href="http://net.nthu.edu.tw/2009/about:contact" target="_blank">http://net.nthu.edu.tw/2009/about:contact</a>)<br />
</span>
<br />
寄信紀錄查詢系統(SMTP Query System)：<a href="http://net.nthu.edu.tw/redirect/smtpquery.htm">http://net.nthu.edu.tw/redirect/smtpquery.htm</a><br />
查詢信箱(Email)：$email<br />
時間範圍(Date)：$date_begin 至 $date_end 的寄信紀錄<br />
查詢來源(Client IP)：$client_ip<br />
EOF
;
    }
}

sub html_footer
{
    $buffer .= <<EOF
</body>
</html>
EOF
;
}

sub sender
{
    my $msg;

    if (length($buffer) > 1024 * 1024) {
        use IO::Compress::Zip qw(zip);
        my $status;
        my $out;
        $status = zip(\$buffer => \$out, Name => "$email.html");

        $msg = MIME::Lite->new(
            From     => 'null@cc.nthu.edu.tw',
            To       => $email,
            Subject  => "Query SMTP logs from $date_begin to $date_end (compressed)",
            Encoding => 'base64',
            Type     => 'application/zip',
            Filename => "$email.zip",
            Data => $out,
        );
    }
    else {
        $msg = MIME::Lite->new(
            From     => 'null@cc.nthu.edu.tw',
            To       => $email,
            Subject  => "Query SMTP logs from $date_begin to $date_end",
            Type     => 'text/html',
            Encoding => 'base64',
            Data     => $buffer,
        );
    }

    $msg->attr('content-type.charset' => 'UTF-8');

    MIME::Lite->send('smtp', 'smtp.cc.nthu.edu.tw', Timeout => 60);

    $msg->send();
}

sub main
{
    getArgvs();

    getParams();

    html_header();

    getSummary();

    $buffer .= <<EOF
<br />信件寄送紀錄
EOF
;

    opendir(DH, "$SMTPLOG_PATH");
    my @dirs = grep {-d "$SMTPLOG_PATH/$_" && m/^\d\d\d\d\-\d\d-\d\d$/ }
                   readdir(DH);
    closedir(DH);

    @dirs = sort(@dirs);

    $buffer .= <<EOF
<table class="stats" border="1">
	<tr>
		<td class="hed" nowrap>項次<br />No.</td>
		<td class="hed" nowrap>寄件者 IP<br />Sender IP</td>
		<td class="hed" nowrap>中繼 SMTP<br />SMTP Relay</td>
		<td class="hed" nowrap>時間<br />Time</td>
		<td class="hed" nowrap>編號<br />ID</td>
		<td class="hed" nowrap>狀態<br />Status</td>
		<td class="hed">回應訊息<br />Response Message</td>
	</tr>
EOF
;

    foreach my $dir (@dirs) {
        if (($dir ge $date_begin) && ($dir le $date_end)) {
            getLogfile($dir);
        }
    }

    $buffer .= <<EOF
</table>
EOF
;

    if ($count > $threshold) {
        my $remain = $count - $threshold;
        $buffer .= <<EOF
<span class="alert">因記錄筆數過多，尚餘 $remain 筆未顯示。</span>
EOF
;
    }

    html_footer();

    sender();
}

main();
