#!/usr/bin/perl -w
#
use strict;
use warnings;
#
BEGIN { $INC{'ValidateCheck.pm'} ||= __FILE__ };

package ValidateCheck;
use LWP::UserAgent;

our @ISA = qw(Exporter);
our @EXPORT = qw(checkRemoteValidate
                );

my $URL = "http://service.oz.nthu.edu.tw/cgi-bin/validate/validate_check.cgi";

sub checkRemoteValidate
{
    my $validate = shift || '';
    my $host     = shift || '';

    $validate =~ s/[^\d]//g;
    $host     =~ s/[^a-zA-Z0-9\.\-\_]//g;

    my $ua = LWP::UserAgent->new;
    $ua->timeout(10);

    my $response = $ua->get("$URL?validate=$validate&host=$host");

    if ($response->is_success) {
        return $response->content;
    }
    else { # bypass
        return -1;
    }
}
