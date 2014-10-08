#!/usr/local/bin/perl -w
#
use strict;
use warnings;
#
use CGI qw(:standard);
#
my $SMTPLOG_PATH = "/logpool/mail_from";
my $URL = "https://service.oz.nthu.edu.tw/cgi-bin/validate/validate.cgi?host=default";

sub main
{
    opendir(DH, "$SMTPLOG_PATH");
    my @dirs = grep {-d "$SMTPLOG_PATH/$_" && m/^\d\d\d\d\-\d\d-\d\d$/ }
                   readdir(DH);
    closedir(DH);
    @dirs = sort(@dirs);

    my $begin_lists = '';
    my $end_lists = '';

    foreach (@dirs[-32..-1]) {
        $begin_lists .= "<option value=\"$_\">$_</option>";
    }

    @dirs = reverse(@dirs);

    foreach (@dirs[0..31]) {
        $end_lists .= "<option value=\"$_\">$_</option>";
    }

    print header(-charset => 'utf-8');

    my $client_ip = $ENV{"REMOTE_ADDR"} || "";

    if ($client_ip !~ m/^140\.114\./) {
        print <<EOF
<html>
<head>
<title>寄信紀錄查詢系統 (SMTP Query System)</title>
</head>
<body>
<pre>
您的 IP 來源為 $client_ip，本系統僅接受國立清華大學校園內的 IP (140.114.0.0/16)。校外可使用 <a href="http://net.nthu.edu.tw/2009/sslvpn:info" target="_blank">TWAREN SSL-VPN</a>。
</pre>
</body>
</html>
EOF
;
        exit(1);
    }

    print <<EOF
<html>
<head>
<title>寄信紀錄查詢系統 (SMTP Query System)</title>
<style>
	body, input, select {
		font-family: Verdana, Geneva, Arial, Helvetica, sans-serif;
		font-size: 12px;
	}

	h2 {
		font-size: 18pt;
	}

	h3 {
		font-size: 16pt;
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
		text-align: right;
		border-bottom: 2px #fff solid;
		font-size: 12px;
		font-weight: bold;
	}
</style>
</head>
<body>
<div align="center">
<h2>寄信紀錄查詢系統</h2>
<h3>SMTP Query System</h3>
<form action="trigger.cgi" method="post">
<input type="hidden" name="host" value="default" />
<table class="stats" border="1">
<tr>
	<td class="hed" nowrap>電子郵件信箱<br />E-mail:</td><td nowrap><input name="email" size="24" /><br />(限本校信箱查詢使用，<br />即 .nthu.edu.tw 結尾)</td>
</tr>
<tr>
	<td class="hed" nowrap>起始時間<br />Begin:</td>
	<td>
		<select name="begin">
		$begin_lists
		</select>
	</td>
</tr>
<tr>
	<td class="hed" nowrap>結束時間<br />End:</td>
	<td>
		<select name="end">
		$end_lists
		</select>
	</td>
</tr>
<tr>
	<td class="hed" nowrap>驗證碼<br />Validate Code:</td>
	<td>
		<img src="$URL" />
		<input type="text" name="validate"  size="8" maxlength="6" />
	</td>
</tr>
<tr>
	<td colspan="2" nowrap>
		<input type="reset" />
		<input type="submit" />
	</td>
</tr>
</table>
</div>
</form>
</body>
</html>
EOF
;
}

main();
