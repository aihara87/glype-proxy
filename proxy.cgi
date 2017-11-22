#!/usr/bin/perl
#
#   CGIProxy 2.1.6
#
#   nph-proxy.cgi-- CGIProxy 2.1: a proxy in the form of a CGI script.
#     Retrieves the resource at any HTTP or FTP URL, updating embedded URLs
#     in HTML and other resources to point back through this script.  By
#     default, no user info is sent to the server.  Options include
#     text-only proxying to save bandwidth, cookie filtering, ad filtering,
#     script removal, user-defined encoding of the target URL, and more.
#     Besides running as a CGI script, can also run under mod_perl, as a
#     FastCGI script, or can use its own embedded HTTP server.
#     Requires Perl 5.
#
#   Copyright (C) 1996, 1998-2013 by James Marshall, james@jmarshall.com
#   All rights reserved.  Free for non-commercial use; commercial use
#   requires a license.
#
#   For the latest, see http://www.jmarshall.com/tools/cgiproxy/
#
#
#   IMPORTANT NOTE ABOUT ANONYMOUS BROWSING:
#     CGIProxy was originally made for indirect browsing more than
#       anonymity, but since people are using it for anonymity, I've tried
#       to make it as anonymous as possible.  Suggestions welcome.  For best
#       anonymity, browse with JavaScript turned off.  That said, please notify
#       me if you find any privacy holes, even when using JavaScript.
#     Anonymity is good, but may not be bulletproof.  For example, if even
#       a single unchecked JavaScript statement can be run, your anonymity
#       can be compromised.  I've tried to handle JS in every place it can
#       exist, but please tell me if I missed any.  Also, browser plugins
#       or other executable extensions may be able to reveal you to a server.
#       Also, be aware that this script doesn't modify PDF files or other
#       third-party document formats that may contain linking ability, so
#       you will lose your anonymity if you follow links in such files.
#     If you find any other way your anonymity can be compromised, please let
#       me know.
#
#
#   CONFIGURATION:
#
#     None required in most situations.  On some servers, these might be
#       required (all in the "user configuration" section):
#       . If you're using a database to store cookies (makes them behave better),
#           you need to set $DB_DRIVER, $DB_USER, and $DB_PASS .  See the notes
#           by those settings for more details.  Note that you should purge
#           the database periodically, with a cron job on Unix or Mac, or with
#           the Task Scheduler in Windows.
#       . If you're using another HTTP or SSL proxy, set $HTTP_PROXY,
#           $SSL_PROXY, and $NO_PROXY as needed.  If those proxies use
#           authentication, set $PROXY_AUTH and $SSL_PROXY_AUTH accordingly.
#       . If this is running on an insecure server that doesn't use port 80, set
#           $RUNNING_ON_SSL_SERVER=0 (otherwise, the default of '' is fine).
#       . If you plan to run CGIProxy as a FastCGI script, set at least
#           $SECRET_PATH and see the configuration section "FastCGI configuration".
#       . If you plan to run CGIProxy using its own embedded server, set
#           $SECRET_PATH and see the configuration section "Embedded server configuration".
#           You'll also need a certificate and private key (key pair) in PEM
#           format.
#
#     Options include:
#       . To install Perl CPAN modules that let you visit secure servers and
#           use compression, run "./nph-proxy.cgi install-modules" from the
#           command line (on Windows, run "perl nph-proxy.cgi install-modules").
#           Ignore the scrolling text, and hit <return> if asked any questions.
#       . Set $TEXT_ONLY, $REMOVE_COOKIES, $REMOVE_SCRIPTS, $FILTER_ADS,
#           $HIDE_REFERER, and $INSERT_ENTRY_FORM as desired.  Set
#           $REMOVE_SCRIPTS if anonymity is important.
#       . To let the user choose all of those settings (except $TEXT_ONLY),
#           set $ALLOW_USER_CONFIG=1.
#       . To change the encoding format of the URL, modify the
#           proxy_encode() and proxy_decode() routines.  The default
#           routines are suitable for simple PATH_INFO compliance.
#       . To encode cookies, modify the cookie_encode() and cookie_decode()
#           routines.
#       . You can restrict which servers this proxy will access, with
#           @ALLOWED_SERVERS and @BANNED_SERVERS.
#       . Similarly, you can specify allowed and denied server lists for
#           both cookies and scripts.
#       . For security, you can ban access to private IP ranges, with
#           @BANNED_NETWORKS.
#       . If filtering ads, you can customize this with a few settings.
#       . To insert your own block of HTML into each page, set $INSERT_HTML
#           or $INSERT_FILE.
#       . As a last resort, if you really can't run this script as NPH,
#           you can try to run it as non-NPH by setting $NOT_RUNNING_AS_NPH=1.
#           BUT, read the notes and warnings above that line.  Caveat surfor.
#       . For crude load-balancing among a set of proxies, set @PROXY_GROUP.
#       . Other config is possible; see the user configuration section.
#       . If heavy use of this proxy puts a load on your server, see the
#           "NOTES ON PERFORMANCE" section below.
#
#     For more info, read the comments above any config options you set.
#
#     This script MUST be installed as a non-parsed header (NPH) script.
#       In Apache and many other servers, this is done by simply starting the
#       filename with "nph-".  It MAY be possible to fake it as a non-NPH
#       script, MOST of the time, by using the $NOT_RUNNING_AS_NPH feature.
#       This is not advised.  See the comments by that option for warnings.
#
#
#   TO USE:
#     Start a browsing session by calling the script with no parameters.
#       You can bookmark pages you browse to through the proxy, or link to
#       the URLs that are generated.
#
#
#   NOTES ON PERFORMANCE:
#     Unfortunately, this has gotten slower through the versions, mostly
#       because of optional new features.  Configured equally, version 1.3
#       takes 25% longer to run than 1.0 or 1.1 (based on *cough* highly
#       abbreviated testing).  Compiling takes about 50% longer.
#     Leaving $REMOVE_SCRIPTS=1 adds 25-50% to the running time.
#     Remember that we're talking about tenths of a second here.  Most of
#       the delay experienced by the user is from waiting on two network
#       connections.  These performance issues only matter if your server
#       CPU is getting overloaded.  Also, these mostly matter when retrieving
#       JavaScript and Flash, because modifying those is what takes most of the
#       time.
#     If you can, use mod_perl.  Starting with version 1.3.1, this should
#       work under mod_perl, which requires Perl 5.004 or later.  If you use
#       mod_perl, be careful to install this as an NPH script, i.e. set the
#       "PerlSendHeader Off" configuration directive (or "PerlOptions -ParseHeaders"
#       if using mod_perl 2.x).  For more info, see the mod_perl documentation.
#     If you can't use mod_perl, try using FastCGI.  Configure the section
#       "FastCGI configuration" below, and run nph-proxy.cgi from the command
#       line to see a usage message.  You'll also need to configure your
#       Web server to use FastCGI.
#     If you can't use mod_perl or FastCGI, try running CGIProxy as its own
#       embedded server.  Configure the section "Embedded server configuration",
#       and run nph-proxy.cgi from the command line to see a usage message.
#       You'll also need a key pair (certificate and private key).
#     If you use mod_perl, FastCGI, or the embedded server, and modify this
#       script, see the note near the "reset 'a-z'" line below, regarding
#       UPPER_CASE and lower_case variable names.
#
#
#   TO DO:
#     What I want to hear about:
#       . Any HTML tags not being converted here.
#       . Any method of introducing JavaScript or other script, that's not
#           being handled here.
#       . Any script MIME types other than those already in @SCRIPT_MIME_TYPES.
#       . Any MIME types other than text/html that have links that need to
#           be converted.
#     plug any other script holes (e.g. MSIE-proprietary, other MIME types?)
#     This could use cleaner URL-encoding all over ($base_url, etc.)
#     more error checking?
#     find a simple encryption technique for proxy_encode()
#     support more protocols, like mailto: or gopher:
#     For ad filtering, add option to disable images from servers other than
#       that of the containing HTML page?  Is it worth it?
#
#
#   BUGS:
#     Anonymity may not not perfect.  In particular, there may be some remaining
#       JavaScript or Flash holes.  Please let me know if you find any.
#     Since ALL of your cookies are sent to this script (which then chooses
#       the relevant ones), some cookies could be dropped if you accumulate a
#       lot, resulting in "Bad Request" errors.  To fix this, use a database
#       server for cookies.
#
#
#   I first wrote this in 1996 as an experiment to allow indirect browsing.
#     The original seed was a program I wrote for Rich Morin's article
#     in the June 1996 issue of Unix Review, online at
#     http://www.cfcl.com/tin/P/199606.shtml.
#
#   Confession: I didn't originally write this with the spec for HTTP
#     proxies in mind, and there are probably some violations of the protocol
#     (at least for proxies).  This whole thing is one big violation of the
#     proxy model anyway, so I hereby rationalize that the spec can be widely
#     interpreted here.  If there is demand, I can make it more conformant.
#     The HTTP client and server components should be fine; it's just the
#     special requirements for proxies that may not be followed.
#
#--------------------------------------------------------------------------

use strict ;
use warnings ;
no warnings qw(uninitialized) ;   # use defaults all the time

use Socket ;
use Encode ;
use IO::Handle ;
use IO::Select ;
use File::Spec ;
use Time::Local ;
use Getopt::Long ;
use Net::Domain qw(hostfqdn) ;
use Fcntl qw(:DEFAULT :flock) ;
use POSIX qw(:sys_wait_h setsid);
use Time::HiRes qw(gettimeofday tv_interval) ;
use Errno qw(EINTR EAGAIN EWOULDBLOCK ENOBUFS EPIPE) ;


# First block below is config variables, second block is sort-of config
#   variables, third block is persistent constants, fourth block is would-be
#   persistent constants (not set until needed), fifth block is constants for
#   JavaScript processing (mostly regular expressions), and last block is
#   variables.
# Removed $RE_JS_STRING_LITERAL to help with Perl's long-literal-string bug,
#   but can replace it later if/when that is fixed.  Added
#   $RE_JS_STRING_LITERAL_START, $RE_JS_STRING_REMAINDER_1, and
#   $RE_JS_STRING_REMAINDER_2 as part of the workaround.
use vars qw(
   $PROXY_DIR  $SECRET_PATH  $LOCAL_LIB_DIR
   $FCGI_SOCKET  $FCGI_MAX_REQUESTS_PER_PROCESS  $FCGI_NUM_PROCESSES
   $PRIVATE_KEY_FILE  $CERTIFICATE_FILE  $RUN_AS_USER  $EMB_USERNAME  $EMB_PASSWORD
   $DB_DRIVER  $DB_NAME  $DB_USER  $DB_PASS  $USE_DB_FOR_COOKIES
   %REDIRECTS
   $TEXT_ONLY
   $REMOVE_COOKIES  $REMOVE_SCRIPTS  $FILTER_ADS  $HIDE_REFERER
   $INSERT_ENTRY_FORM  $ALLOW_USER_CONFIG
   $ENCODE_DECODE_BLOCK_IN_JS
   @ALLOWED_SERVERS  @BANNED_SERVERS  @BANNED_NETWORKS
   $NO_COOKIE_WITH_IMAGE  @ALLOWED_COOKIE_SERVERS  @BANNED_COOKIE_SERVERS
   @ALLOWED_SCRIPT_SERVERS  @BANNED_SCRIPT_SERVERS
   @BANNED_IMAGE_URL_PATTERNS  $RETURN_EMPTY_GIF
   $USER_IP_ADDRESS_TEST  $DESTINATION_SERVER_TEST
   $INSERT_HTML  $INSERT_FILE  $ANONYMIZE_INSERTION  $FORM_AFTER_INSERTION
   $INSERTION_FRAME_HEIGHT
   $RUNNING_ON_SSL_SERVER  $NOT_RUNNING_AS_NPH
   $HTTP_PROXY  $SSL_PROXY  $NO_PROXY  $PROXY_AUTH  $SSL_PROXY_AUTH
   $MINIMIZE_CACHING
   $SESSION_COOKIES_ONLY  $COOKIE_PATH_FOLLOWS_SPEC  $RESPECT_THREE_DOT_RULE
   @PROXY_GROUP
   $USER_AGENT  $USE_PASSIVE_FTP_MODE  $SHOW_FTP_WELCOME
   $PROXIFY_SCRIPTS  $PROXIFY_SWF  $ALLOW_RTMP_PROXY  $ALLOW_UNPROXIFIED_SCRIPTS
   $PROXIFY_COMMENTS
   $USE_POST_ON_START  $ENCODE_URL_INPUT
   $REMOVE_TITLES  $NO_BROWSE_THROUGH_SELF  $NO_LINK_TO_START  $MAX_REQUEST_SIZE
   @TRANSMIT_HTML_IN_PARTS_URLS
   $QUIETLY_EXIT_PROXY_SESSION
   $OVERRIDE_SECURITY

   @SCRIPT_MIME_TYPES  @OTHER_TYPES_TO_REGISTER  @TYPES_TO_HANDLE
   $NON_TEXT_EXTENSIONS
   $PROXY_VERSION

   $RUN_METHOD
   @MONTH  @WEEKDAY  %UN_MONTH
   @BANNED_NETWORK_ADDRS
   $DBH  $STH_UPD_COOKIE  $STH_INS_COOKIE  $STH_SEL_COOKIE  $STH_SEL_ALL_COOKIES
   $STH_DEL_COOKIE  $STH_UPD_SESSION  $STH_INS_SESSION  $STH_SEL_IP
   $STH_PURGE_SESSIONS  $STH_PURGE_COOKIES
   $USER_IP_ADDRESS_TEST_H  $DESTINATION_SERVER_TEST_H
   $RUNNING_ON_IIS
   @NO_PROXY
   $NO_CACHE_HEADERS
   @ALL_TYPES  %MIME_TYPE_ID  $SCRIPT_TYPE_REGEX  $TYPES_TO_HANDLE_REGEX
   $THIS_HOST  $ENV_SERVER_PORT  $ENV_SCRIPT_NAME  $THIS_SCRIPT_URL
   $RTMP_SERVER_PORT
   %ENV_UNCHANGING  $HAS_INITED

   $CUSTOM_INSERTION  %IN_CUSTOM_INSERTION

   $RE_JS_WHITE_SPACE  $RE_JS_LINE_TERMINATOR  $RE_JS_COMMENT
   $RE_JS_IDENTIFIER_START  $RE_JS_IDENTIFIER_PART  $RE_JS_IDENTIFIER_NAME
   $RE_JS_PUNCTUATOR  $RE_JS_DIV_PUNCTUATOR
   $RE_JS_NUMERIC_LITERAL  $RE_JS_ESCAPE_SEQUENCE
   $RE_JS_STRING_LITERAL
   $RE_JS_STRING_LITERAL_START  $RE_JS_STRING_REMAINDER_1  $RE_JS_STRING_REMAINDER_2
   $RE_JS_REGULAR_EXPRESSION_LITERAL
   $RE_JS_TOKEN  $RE_JS_INPUT_ELEMENT_DIV  $RE_JS_INPUT_ELEMENT_REG_EXP
   $RE_JS_SKIP  $RE_JS_SKIP_NO_LT
   %RE_JS_SET_TRAPPED_PROPERTIES %RE_JS_SET_RESERVED_WORDS_NON_EXPRESSION
   %RE_JS_SET_ALL_PUNCTUATORS
   $JSLIB_BODY

   $HTTP_VERSION  $HTTP_1_X
   $URL
   $STDIN  $STDOUT
   $now  $session_id  $session_id_persistent  $session_cookies
   $packed_flags  $encoded_URL  $doing_insert_here  $env_accept
   $e_remove_cookies  $e_remove_scripts  $e_filter_ads  $e_insert_entry_form
   $e_hide_referer
   $images_are_banned_here  $scripts_are_banned_here  $cookies_are_banned_here
   $scheme  $authority  $path  $host  $port  $username  $password
   $cookie_to_server  %auth
   $script_url  $url_start  $url_start_inframe  $url_start_noframe
   $is_in_frame  $expected_type
   $base_url  $base_scheme  $base_host  $base_path  $base_file  $base_unframes
   $default_style_type  $default_script_type
   $status  $headers  $body  $charset  $is_html  $response_sent
   %in_mini_start_form
   $needs_jslib  $does_write
   $swflib  $AVM2_BYTECODES
   $debug ) ;


#--------------------------------------------------------------------------
#    user configuration
#--------------------------------------------------------------------------

# [As of 2.1.6, this is only needed if using the embedded server.]
# For certain purposes, CGIProxy may need to create files.  This is where
#   those will go.  For example, use "/home/username/cgiproxy", where "username"
#   is replaced by your username.
# This must be an absolute path to the directory, i.e. a path starting with
#   "/" or "\" (possibly after a drive letter and ":" if using Windows).  Note that
#   you need to use "\\" to represent a single backslash.
# Leading drive letters (e.g. for Windows) are allowed.
# The default will use the directory "cgiproxy" under your home directory (which
#   varies with your operating system).  If it doesn't work, manually set
#   $PROXY_DIR to an absolute path.  You can name it whatever you want.
# Note that in Unix or Mac, using a directory on a mounted filesystem (which often
#   includes home directories) may prevent that filesystem from being unmounted,
#   which may bother your sysadmin.  If so, try setting this to something starting
#   with "/tmp/", like "/tmp/.yourname/".
# If you get "mkdir" permission errors, create the directory yourself with mkdir.
#   You may also need to "chmod 777 directoryname" to make the directory writable
#   by the Web server, but note that this makes it readable and writable by
#   everybody.  You might ask your webmaster if they provide a safe way for CGI
#   scripts to read and write files in your directories.
$PROXY_DIR= $^O=~ /win/i  ? "$ENV{HOMEDRIVE}$ENV{HOMEPATH}\\cgiproxy"  # Windows
			  : "$ENV{HOME}/cgiproxy" ;                    # Unix and Mac
#$PROXY_DIR= '/absolute/path/here/cgiproxy' ;      # if you need to set it manually


# IMPORTANT:  CHANGE THIS IF USING FASTCGI OR THE EMBEDDED SERVER!
# If using FastCGI or the embedded server, the path in the URL will begin with a
#   fixed alphanumeric sequence (string) to help conceal the proxy.  You can set
#   this to any alphanumeric string.  The URL of your proxy will be
#   "https://example.com/secret" (replace "secret" with your actual secret).
# If we didn't do this, then a censor could check if a site hosts a proxy by
#   merely accessing "https://example.com" .
# Note that this is not a secret from the users, just from anyone watching
#   network traffic.  Also, it won't be kept secret if your server is insecure.
$SECRET_PATH= 'secret' ;


# If this script is not running as your user ID (such as a Web server running
#   as its own user ID), and you're using the local::lib module, then 
#   set this to the directory where your modules are installed with local::lib .
#   This is normally just the "perl5" directory under your home directory, unless
#   you renamed it or configured lib::local to use a different directory.
# If you set this before installing modules, then modules will be installed
#   into this directory.
#$LOCAL_LIB_DIR= '/home/your-username/perl5' ;   # this example works for Unix or Mac


#---- FastCGI configuration ---------------------

# FastCGI is a mechanism that can speed up CGI-like scripts.  It's purely
#   optional and requires some web server configuration as well, and if you
#   don't use it you can ignore this section.

# FastCGI uses a Unix-domain socket to communicate between the FastCGI client
#   (e.g. the web server software) and the FastCGI server (e.g. a CGI script
#   that has been converted to run as a listening daemon, such as CGIProxy).
#   A "Unix-domain socket" looks like a file in a directory listing, but is
#   actually a mechanism to allow different processes to communicate with
#   each other.
# If that's confusing, just set this to an absolute path/filename in a
#   directory that can be read and written by the web server.  The default is
#   usually fine on Unix or Mac systems.  You'll also need to configure your
#   web server to use the same path/filename.
# It's also possible to use a normal Internet socket on the same machine,
#   though that's less efficient than a Unix-domain socket.  If you do use
#   an Internet socket, set $FCGI_SOCKET equal to a colon followed by a
#   local port, e.g. ":1234".
$FCGI_SOCKET= '/tmp/cgiproxy.fcgi.socket' ;


# FastCGI uses multiple processes to listen on its socket, where each
#   process can handle one request at a time.  This is a performance tuning
#   parameter, so the optimal number depends on your server environment
#   (hardware and software).
# If you don't understand this, the default should be fine.  You can experiment
#   with different numbers if performance is an issue.
# This can be overridden with the "-n" command-line parameter.
$FCGI_NUM_PROCESSES= 100 ;


# As a FastCGI process gets used for many requests, it slowly takes more and
#   more memory, due to the copy-on-write behavior of forked processes.  Thus,
#   it's cleaner if you kill a process and restart a fresh one after it handles
#   some number of requests.  This is a performance tuning parameter, so the
#   optimal number depends on your server environment (hardware and software).
# If you don't understand this, the default should be fine.  You can experiment
#   with different numbers if performance is an issue.
# This can be overridden with the "-m" command-line parameter.
$FCGI_MAX_REQUESTS_PER_PROCESS= 1000 ;


#---- End of FastCGI configuration --------------

# Much initialization of unchanging values is now in this routine.  (Ignore
#   this if you don't know what it means.)
sub init {


#---- Embedded server configuration -------------

# For the embedded server, you need to a) put a certificate and private key,
#   in PEM format, into the $PROXY_DIR directory, and b) set these two
#   variables to the two file names.  (A "certificate" is the same thing as
#   a public key.)
# You can either pay a certificate authority for a key pair, or you can
#   generate your own "self-signed" key pair.  The disadvantage of using a
#   self-signed key pair is that your users will see a browser warning about
#   an untrusted certificate.  This is all true of any secure server.
#$CERTIFICATE_FILE= 'plain-cert.pem' ;
#$PRIVATE_KEY_FILE= 'plain-rsa.pem' ;


# If you run this as the root user to use port 443, it's a good idea to change
#   the user ID to something with fewer permissions.  You can set this to either
#   a username, or a numeric user ID.
# This probably won't work on Windows.
$RUN_AS_USER= 'nobody' ;


# It's important to use $SECRET_PATH, but you can require a username and
#   password too.  All users must login with whatever you set below, using
#   HTTP Basic authentication.  Leave these commented out to disable
#   password protection.
# This is very simple right now.  In the future there will likely be
#   more authentication methods, including support for multiple users.
#$EMB_USERNAME= 'free' ;
#$EMB_PASSWORD= 'speech' ;


#---- End of embedded server configuration ------


#---- Database configuration --------------------

# Database use is optional, and if you don't use one you can ignore this
#   section.  But if you're getting "Bad Request" errors, you can fix it
#   by using a database; also, see the $USE_DB_FOR_COOKIES option below.

# Database use is optional.  It's most efficient when this script is running
#   under mod_perl or FastCGI.
# To use a database, create a database account for this program to use, or ask
#   your database administrator to do it.  Set $DB_USER and $DB_PASS to the
#   username and password, below.  This program will try to create the required
#   database, named $DB_NAME as set below, but if your DBA isn't willing to grant the
#   permission to create databases to the CGIProxy user, then you or the DBA will
#   need to create the database.
#
# If you are using a database, it must be purged periodically.  In Unix or
#   Mac, do this with a cron job.  In Windows, use the Task Scheduler.
# In Unix or Mac, the command to purge the database is
#   "/path/to/script/nph-proxy.cgi -c purge-db".  (Replace "/path/to/script/"
#   with the actual path to the script.)  Edit your crontab with "crontab -e",
#   and add a line like:
#     "0 * * * * /path/to/script/nph-proxy.cgi -c purge-db" (without quotes)
#   to purge the database at the top of every hour, or:
#     "0 2 * * * /path/to/script/nph-proxy.cgi -c purge-db" (without quotes)
#   to purge it every night at 2:00am.


# This is the name of the "database driver" for the database software you're using.
#   Currently supported values are "MySQL" and "Oracle".
# Leave this empty or commented out to not use a database, or set it to use
#   a database.
#$DB_DRIVER= 'MySQL' ;


# CGIProxy creates (if possible) and uses its own database.  If you want to name
#   the database something else, change this value.  If you need a database
#   administrator to create the database, tell him or her this database name.
$DB_NAME= 'cgiproxy' ;


# These are the username and password of the database account, as described above.
$DB_USER= 'proxy' ;
$DB_PASS= '' ;


# If set, then use the server-side database to store cookies.  This gets around
#   the problem of too many total cookies causing "Bad Request" errors.
# Set this to 1 to use the database (if it's configured), or to 0 to NOT use
#   the database.
$USE_DB_FOR_COOKIES= 1 ;


#---- End of database configuration -------------



# If set, then proxy traffic will be restricted to text data only, to save
#   bandwidth (though it can still be circumvented with uuencode, etc.).
# To replace images with a 1x1 transparent GIF, set $RETURN_EMPTY_GIF below.
$TEXT_ONLY= 0 ;      # set to 1 to allow only text data, 0 to allow all


# If set, then prevent all cookies from passing through the proxy.  To allow
#   cookies from some servers, set this to 0 and see @ALLOWED_COOKIE_SERVERS
#   and @BANNED_COOKIE_SERVERS below.  You can also prevent cookies with
#   images by setting $NO_COOKIE_WITH_IMAGE below.
# Note that this only affects cookies from the target server.   The proxy
#   script sends its own cookies for other reasons too, like to support
#   authentication.  This flag does not stop these cookies from being sent.
$REMOVE_COOKIES= 0 ;


# If set, then remove as much scripting as possible.  If anonymity is
#   important, this is strongly recommended!  Better yet, turn off script
#   support in your browser.
# On the HTTP level:
#   . prevent transmission of script MIME types (which only works if the server
#       marks them as such, so a malicious server could get around this, but
#       then the browser probably wouldn't execute the script).
#   . remove Link: headers that link to a resource of a script MIME type.
# Within HTML resources:
#   . remove <script>...</script> .
#   . remove intrinsic event attributes from tags, i.e. attributes whose names
#       begin with "on".
#   . remove <style>...</style> where "type" attribute is a script MIME type.
#   . remove various HTML tags that appear to link to a script MIME type.
#   . remove script macros (aka Netscape-specific "JavaScript entities"),
#       i.e. any attributes containing the string "&{" .
#   . remove "JavaScript conditional comments".
#   . remove MSIE-specific "dynamic properties".
# To allow scripts from some sites but not from others, set this to 0 and
#   see @ALLOWED_SCRIPT_SERVERS and @BANNED_SCRIPT_SERVERS below.
# See @SCRIPT_MIME_TYPES below for a list of which MIME types are filtered out.
# I do NOT know for certain that this removes all script content!  It removes
#   all that I know of, but I don't have a definitive list of places scripts
#   can exist.  If you do, please send it to me.  EVEN RUNNING A SINGLE
#   JAVASCRIPT STATEMENT CAN COMPROMISE YOUR ANONYMITY!  Just so you know.
# Richard Smith has a good test site for anonymizing proxies, at
#   http://users.rcn.com/rms2000/anon/test.htm
# Note that turning this on removes most popup ads!  :)
$REMOVE_SCRIPTS= 0 ;


# If set, then filter out images that match one of @BANNED_IMAGE_URL_PATTERNS,
#   below.  Also removes cookies attached to images, as if $NO_COOKIE_WITH_IMAGE
#   is set.
# To remove most popup advertisements, also set $REMOVE_SCRIPTS=1 above.
$FILTER_ADS= 0 ;


# If set, then don't send a Referer: [sic] header with each request
#   (i.e. something that tells the server which page you're coming from
#   that linked to it).  This is a minor privacy issue, but a few sites
#   won't send you pages or images if the Referer: is not what they're
#   expecting.  If a page is loading without images or a link seems to be
#   refused, then try turning this off, and a correct Referer: header will
#   be sent.
# This is only a problem in a VERY small percentage of sites, so few that
#   I'm kinda hesitant to put this in the entry form.  Other arrangements
#   have their own problems, though.
$HIDE_REFERER= 0 ;


# If set, insert a compact version of the URL entry form at the top of each
#   page.  This will also display the URL currently being viewed.
# When viewing a page with frames, then a new top frame is created and the
#   insertion goes there.
# If you want to customize the appearance of the form, modify the routine
#   mini_start_form() near the end of the script.
# If you want to insert something other than this form, see $INSERT_HTML and
#   $INSERT_FILE below.
# Users should realize that options changed via the form only take affect when
#   the form is submitted by entering a new URL or pressing the "Go" button.
#   Selecting an option, then following a link on the page, will not cause
#   the option to take effect.
# Users should also realize that anything inserted into a page may throw
#   off any precise layout.  The insertion will also be subject to
#   background colors and images, and any other page-wide settings.
$INSERT_ENTRY_FORM= 1 ;


# If set, then allow the user to control $REMOVE_COOKIES, $REMOVE_SCRIPTS,
#   $FILTER_ADS, $HIDE_REFERER, and $INSERT_ENTRY_FORM.  Note that they
#   can't fine-tune any related options, such as the various @ALLOWED... and
#   @BANNED... lists.
$ALLOW_USER_CONFIG= 1 ;



# If you want to encode the URLs of visited pages so that they don't show
#   up within the full URL in your browser bar, then use proxy_encode() and
#   proxy_decode().  These are Perl routines that transform the way the
#   destination URL is included in the full URL.  You can either use
#   some combination of the example encodings below, or you can program your
#   own routines.  The encoded form of URLs should only contain characters
#   that are legal in PATH_INFO.  This varies by server, but using only
#   printable chars and no "?" or "#" works on most servers.  Don't let
#   PATH_INFO contain the strings "./", "/.", "../", or "/..", or else it
#   may get compressed like a pathname somewhere.  Try not to make the
#   resulting string too long, either.
# Of course, proxy_decode() must exactly undo whatever proxy_encode() does.
# Make proxy_encode() as fast as possible-- it's a bottleneck for the whole
#   program.  The speed of proxy_decode() is not as important.
# If you're not a Perl programmer, you can use the example encodings that are
#   commented out, i.e. the lines beginning with "#".  To use them, merely
#   uncomment them, i.e. remove the "#" at the start of the line.  If you
#   uncomment a line in proxy_encode(), you MUST uncomment the corresponding
#   line in proxy_decode() (note that "corresponding lines" in
#   proxy_decode() are in reverse order of those in proxy_encode()).  You
#   can use one, two, or all three encodings at the same time, as long as
#   the correct lines are uncommented.
# Starting in version 2.1beta9, don't call these functions directly.  Rather,
#   call wrap_proxy_encode() and wrap_proxy_decode() instead, which handle
#   certain details that you shouldn't have to worry about in these functions.
# IMPORTANT: If you modify these routines, and if $PROXIFY_SCRIPTS is set
#   below (on by default), then you MUST modify $ENCODE_DECODE_BLOCK_IN_JS
#   below!!  (You'll need to write corresponding routines in JavaScript to do
#   the same as these routines in Perl, used when proxifying JavaScript.)
# Because of the simplified absolute URL resolution in full_url(), there may
#   be ".." segments in the default encoding here, notably in the first path
#   segment.  Normally, that's just an HTML mistake, but please tell me if
#   you see any privacy exploit with it.
# Note that a few sites have embedded applications (like applets or Shockwave)
#   that expect to access URLs relative to the page's URL.  This means they
#   may not work if the encoded target URL can't be treated like a base URL,
#   e.g. that it can't be appended with something like "../data/foo.data"
#   to get that expected data file.  In such cases, the default encoding below
#   should let these sites work fine, as should any other encoding that can
#   support URLs relative to it.

sub proxy_encode {
    my($URL)= @_ ;
    $URL=~ s#^([\w+.-]+)://#$1/# ;                 # http://xxx -> http/xxx
#    $URL=~ s/(.)/ sprintf('%02x',ord($1)) /ge ;   # each char -> 2-hex
#    $URL=~ tr/a-zA-Z/n-za-mN-ZA-M/ ;              # rot-13

    return $URL ;
}

sub proxy_decode {
    my($enc_URL)= @_ ;

#    $enc_URL=~ tr/a-zA-Z/n-za-mN-ZA-M/ ;        # rot-13
#    $enc_URL=~ s/([\da-fA-F]{2})/ sprintf("%c",hex($1)) /ge ;
    $enc_URL=~ s#^([\w+.-]+)/#$1://# ;           # http/xxx -> http://xxx
    return $enc_URL ;
}


# Encode cookies before they're sent back to the user.
# The return value must only contain characters that are legal in cookie
#   names and values, i.e. only printable characters, and no ";", ",", "=",
#   or white space.
# cookie_encode() is called twice for each cookie: once to encode the cookie
#   name, and once to encode the cookie value.  The two are then joined with
#   "=" and sent to the user.
# cookie_decode() must exactly undo whatever cookie_encode() does.
# Also, cookie_encode() must always encode a given input string into the
#   same output string.  This is because browsers need the cookie name to
#   identify and manage a cookie, so the name must be consistent.
# This is not a bottleneck like proxy_encode() is, so speed is not critical.
# IMPORTANT: If you modify these routines, and if $PROXIFY_SCRIPTS is set
#   below (on by default), then you MUST modify $ENCODE_DECODE_BLOCK_IN_JS
#   below!!  (You'll need to write corresponding routines in JavaScript to do
#   the same as these routines in Perl, used when proxifying JavaScript.)

sub cookie_encode {
    my($cookie)= @_ ;
#    $cookie=~ s/(.)/ sprintf('%02x',ord($1)) /ge ;   # each char -> 2-hex
#    $cookie=~ tr/a-zA-Z/n-za-mN-ZA-M/ ;              # rot-13
    $cookie=~ s/(\W)/ '%' . sprintf('%02x',ord($1)) /ge ; # simple URL-encoding
    return $cookie ;
}

sub cookie_decode {
    my($enc_cookie)= @_ ;
    $enc_cookie=~ s/%([\da-fA-F]{2})/ pack('C', hex($1)) /ge ;  # URL-decode
#    $enc_cookie=~ tr/a-zA-Z/n-za-mN-ZA-M/ ;          # rot-13
#    $enc_cookie=~ s/([\da-fA-F]{2})/ sprintf("%c",hex($1)) /ge ;
    return $enc_cookie ;
}


# If $PROXIFY_SCRIPTS is true, and if you modify the routines above that
#   encode cookies and URLs, then you need to modify $ENCODE_DECODE_BLOCK_IN_JS
#   here.  Explanation:  When proxifying JavaScript, a library of JavaScript
#   functions is used.  In that library are a few JavaScript routines that do
#   the same as their Perl counterparts in this script.  Four of those routines
#   are proxy_encode(), proxy_decode(), cookie_encode(), and cookie_decode().
#   Thus, unfortunately, when you write your own versions of those Perl routines
#   (or modify what's already there), you also need to write (or modify) these
#   corresponding JavaScript routines to do the same thing.  Put the routines in
#   this long variable $ENCODE_DECODE_BLOCK_IN_JS, and it will be included in
#   the JavaScript library when needed.  Prefix the function names with
#   "_proxy_jslib_", as below.
# The commented examples in the JavaScript routines below correspond exactly to
#   the commented examples in the Perl routines above.  Thus, if you modify the
#   Perl routines by merely uncommenting the examples, you can do the same in
#   these JavaScript routines.  (JavaScript comments begin with "//".)
# [If you don't know Perl:  Note that everything up until the line "EOB" is one
#   long string value, called a "here document".  $ENCODE_DECODE_BLOCK_IN_JS is
#   set to the whole thing.]

$ENCODE_DECODE_BLOCK_IN_JS= <<'EOB' ;

function _proxy_jslib_proxy_encode(URL) {
    URL= URL.replace(/^([\w\+\.\-]+)\:\/\//, '$1/') ;
//    URL= URL.replace(/(.)/g, function (s,p1) { return p1.charCodeAt(0).toString(16) } ) ;
//    URL= URL.replace(/([a-mA-M])|[n-zN-Z]/g, function (s,p1) { return String.fromCharCode(s.charCodeAt(0)+(p1?13:-13)) }) ;

    return URL ;
}

function _proxy_jslib_proxy_decode(enc_URL) {
//    enc_URL= enc_URL.replace(/([a-mA-M])|[n-zN-Z]/g, function (s,p1) { return String.fromCharCode(s.charCodeAt(0)+(p1?13:-13)) }) ;
//    enc_URL= enc_URL.replace(/([\da-fA-F]{2})/g, function (s,p1) { return String.fromCharCode(eval('0x'+p1)) } ) ;
    enc_URL= enc_URL.replace(/^([\w\+\.\-]+)\//, '$1://') ;
    return enc_URL ;
}

function _proxy_jslib_cookie_encode(cookie) {
//    cookie= cookie.replace(/(.)/g, function (s,p1) { return p1.charCodeAt(0).toString(16) } ) ;
//    cookie= cookie.replace(/([a-mA-M])|[n-zN-Z]/g, function (s,p1) { return String.fromCharCode(s.charCodeAt(0)+(p1?13:-13)) }) ;
    cookie= cookie.replace(/(\W)/g, function (s,p1) { return '%'+p1.charCodeAt(0).toString(16) } ) ;
    return cookie ;
}

function _proxy_jslib_cookie_decode(enc_cookie) {
    enc_cookie= enc_cookie.replace(/%([\da-fA-F]{2})/g, function (s,p1) { return String.fromCharCode(eval('0x'+p1)) } ) ;
//    enc_cookie= enc_cookie.replace(/([a-mA-M])|[n-zN-Z]/g, function (s,p1) { return String.fromCharCode(s.charCodeAt(0)+(p1?13:-13)) }) ;
//    enc_cookie= enc_cookie.replace(/([\da-fA-F]{2})/g, function (s,p1) { return String.fromCharCode(eval('0x'+p1)) } ) ;
    return enc_cookie ;
}

EOB



# Use @ALLOWED_SERVERS and @BANNED_SERVERS to restrict which servers a user
#   can visit through this proxy.  Any URL at a host matching a pattern in
#   @BANNED_SERVERS will be forbidden.  In addition, if @ALLOWED_SERVERS is
#   not empty, then access is allowed *only* to servers that match a pattern
#   in it.  In other words, @BANNED_SERVERS means "ban these servers", and
#   @ALLOWED_SERVERS (if not empty) means "allow only these servers".  If a
#   server matches both lists, it is banned.
# These are each a list of Perl 5 regular expressions (aka patterns or
#   regexes), not literal host names.  To turn a hostname into a pattern,
#   replace every "." with "\.", add "^" to the beginning, and add "$" to the
#   end.  For example, 'www.example.com' becomes '^www\.example\.com$'.  To
#   match *every* host ending in something, leave out the "^".  For example,
#   '\.example\.com$' matches every host ending in ".example.com".  For more
#   details about Perl regular expressions, see the Perl documentation.  (They
#   may seem cryptic at first, but they're very powerful once you know how to
#   use them.)
# Note: Use single quotes around each pattern, not double qoutes, unless you
#   understand the difference between the two in Perl.  Otherwise, characters
#   like "$" and "\" may not be handled the way you expect.
@ALLOWED_SERVERS= () ;
@BANNED_SERVERS= () ;


# If @BANNED_NETWORKS is set, then forbid access to these hosts or networks.
# This is done by IP address, not name, so it provides more certain security
#   than @BANNED_SERVERS above.
# Specify each element as a decimal IP address-- all four integers for a host,
#   or one to three integers for a network.  For example, '127.0.0.1' bans
#   access to the local host, and '192.168' bans access to all IP addresses
#   in the 192.168 network.  Sorry, no banning yet for subnets other than
#   8, 16, or 24 bits.
# IF YOU'RE RUNNING THIS ON OR INSIDE A FIREWALL, THIS SETTING IS STRONGLY
#   RECOMMENDED!!  In particular, you should ban access to other machines
#   inside the firewall that the firewall machine itself may have access to.
#   Otherwise, external users will be able to access any internal hosts that
#   the firewall can access.  Even if that's what you intend, you should ban
#   access to any hosts that you don't explicitly want to expose to outside
#   users.
# In addition to the recommended defaults below, add all IP addresses of your
#   server machine if you want to protect it like this.
# After you set this, YOU SHOULD TEST to verify that the proxy can't access
#   the IP addresses you're banning!
# NOTE:  According to RFC 1918, network address ranges reserved for private
#   networks are 10.x.x.x, 192.168.x.x, and 172.16.x.x-172.31.x.x, i.e. with
#   respective subnet masks of 8, 16, and 12 bits.  Since we can't currently
#   do a 12-bit mask, we'll exclude the entire 172 network here.  If this
#   causes a problem, let me know and I'll add subnet masks down to 1-bit
#   resolution.
# Also included are 169.254.x.x (per RFC 3927) and 244.0.0.x (used for
#   routing), as recommended by Waldo Jaquith.
# On some systems, 127.x.x.x all point to localhost, so disallow all of "127".
# This feature is simple now but may be more complete in future releases.
#   How would you like this to be extended?  What would be useful to you?
@BANNED_NETWORKS= ('127', '192.168', '172', '10', '169.254', '244.0.0') ;


# Settings to fine-tune cookie filtering, if cookies are not banned altogether
#   (by user checkbox or $REMOVE_COOKIES above).
# Use @ALLOWED_COOKIE_SERVERS and @BANNED_COOKIE_SERVERS to restrict which
#   servers can send cookies through this proxy.  They work like
#   @ALLOWED_SERVERS and @BANNED_SERVERS above, both in how their precedence
#   works, and that they're lists of Perl 5 regular expressions.  See the
#   comments there for details.

# If non-empty, only allow cookies from servers matching one of these patterns.
# Comment this out to allow all cookies (subject to @BANNED_COOKIE_SERVERS).
#@ALLOWED_COOKIE_SERVERS= ('\bslashdot\.org$') ;

# Reject cookies from servers matching these patterns.
@BANNED_COOKIE_SERVERS= (
    '\.doubleclick\.net$',
    '\.preferences\.com$',
    '\.imgis\.com$',
    '\.adforce\.com$',
    '\.focalink\.com$',
    '\.flycast\.com$',
    '\.avenuea\.com$',
    '\.linkexchange\.com$',
    '\.pathfinder\.com$',
    '\.burstnet\.com$',
    '\btripod\.com$',
    '\bgeocities\.yahoo\.com$',
    '\.mediaplex\.com$',
    ) ;

# Set this to reject cookies returned with images.  This actually prevents
#   cookies returned with any non-text resource.
# This helps prevent tracking by ad networks, but there are also some
#   legitimate uses of attaching cookies to images, such as captcha, so
#   by default this is off.
$NO_COOKIE_WITH_IMAGE= 0 ;


# Settings to fine-tune script filtering, if scripts are not banned altogether
#   (by user checkbox or $REMOVE_SCRIPTS above).
# Use @ALLOWED_SCRIPT_SERVERS and @BANNED_SCRIPT_SERVERS to restrict which
#   servers you'll allow scripts from.  They work like @ALLOWED_SERVERS and
#   @BANNED_SERVERS above, both in how their precedence works, and that
#   they're lists of Perl 5 regular expressions.  See the comments there for
#   details.
@ALLOWED_SCRIPT_SERVERS= () ;
@BANNED_SCRIPT_SERVERS= () ;



# Various options to help filter ads and stop cookie-based privacy invasion.
# These are only effective if $FILTER_ADS is set above.
# @BANNED_IMAGE_URL_PATTERNS uses Perl patterns.  If an image's URL
#   matches one of the patterns, it will not be downloaded (typically for
#   ad-filtering).  For more information on Perl regular expressions, see
#   the Perl documentation.
# Note that most popup ads will be removed if scripts are removed (see
#   $REMOVE_SCRIPTS above).
# If ad-filtering is your primary motive, consider using one of the many
#   proxies that specialize in that.  The classic is from JunkBusters, at
#   http://www.junkbusters.com .

# Reject images whose URL matches any of these patterns.  This is just a
#   sample list; add more depending on which sites you visit.
@BANNED_IMAGE_URL_PATTERNS= (
    'ad\.doubleclick\.net/ad/',
    '\b[a-z](\d+)?\.doubleclick\.net(:\d*)?/',
    '\.imgis\.com\b',
    '\.adforce\.com\b',
    '\.avenuea\.com\b',
    '\.go\.com(:\d*)?/ad/',
    '\.eimg\.com\b',
    '\bexcite\.netscape\.com(:\d*)?/.*/promo/',
    '/excitenetscapepromos/',
    '\.yimg\.com(:\d*)?.*/promo/',
    '\bus\.yimg\.com/[a-z]/(\w\w)/\1',
    '\bus\.yimg\.com/[a-z]/\d-/',
    '\bpromotions\.yahoo\.com(:\d*)?/promotions/',
    '\bcnn\.com(:\d*)?/ads/',
    'ads\.msn\.com\b',
    '\blinkexchange\.com\b',
    '\badknowledge\.com\b',
    '/SmartBanner/',
    '\bdeja\.com/ads/',
    '\bimage\.pathfinder\.com/sponsors',
    'ads\.tripod\.com',
    'ar\.atwola\.com/image/',
    '\brealcities\.com/ads/',
    '\bnytimes\.com/ad[sx]/',
    '\busatoday\.com/sponsors/',
    '\busatoday\.com/RealMedia/ads/',
    '\bmsads\.net/ads/',
    '\bmediaplex\.com/ads/',
    '\batdmt\.com/[a-z]/',
    '\bview\.atdmt\.com/',
    '\bADSAdClient31\.dll\b',
    ) ;

# If set, replace banned images with 1x1 transparent GIF.  This also replaces
#   all images with the same if $TEXT_ONLY is set.
# Note that setting this makes the response a little slower, since the browser
#   must still retrieve the empty GIF.
$RETURN_EMPTY_GIF= 0 ;



# To use an external program to decide whether or not a user at a given IP
#   address may use this proxy (as opposed to using server configuration), set
#   $USER_IP_ADDRESS_TEST to either the name of a command-line program that
#   performs this test, or a queryable URL that performs this test (e.g. a CGI
#   script).
# For a command-line program:  The program should take a single argument, the
#   IP address of the user.  The output of the program is evaluated as a
#   number, and if the number is non-zero then the IP address of the user is
#   allowed; thus, the output is typically either "1" or "0".  Note that
#   depending on $ENV{PATH}, you may need to enter the path here explicitly.
# For a queryable URL:  Specify the start of the URL here (must begin with
#   "http://"), and the user's IP address will be appended.  For example, the
#   value here may contain a "?", thus putting the IP address in the
#   QUERY_STRING; it could also be in PATH_INFO.  The response body from the
#   URL should be a number like for a command line program, above.
$USER_IP_ADDRESS_TEST= '' ;


# To use an external program to decide whether or not a destination server is
#   allowed (as opposed to using @ALLOWED_SERVERS and @BANNED_SERVERS above),
#   set $DESTINATION_SERVER_TEST to either the name of a command-line program
#   that performs this test, or a queryable URL that performs this test (e.g. a
#   CGI script).
# For a command-line program: The program should take a single argument, the
#   destination server's name or IP address (depending on how the user enters
#   it).  The output of the program is evaluated as a number, and if the number
#   is non-zero then the destination server is allowed; thus, the output is
#   typically either "1" or "0".  Note that depending on $ENV{PATH}, you may
#   need to enter the path here explicitly.
# For a queryable URL: Specify the start of the URL here (must begin with
#   "http://"), and the destination server's name or IP address will be
#   appended.  For example, the value here may contain a "?", thus putting the
#   name or address in the QUERY_STRING; it could also be in PATH_INFO.  The
#   response body from the URL should be a number like for a command line
#   program, above.
$DESTINATION_SERVER_TEST= '' ;



# If either $INSERT_HTML or $INSERT_FILE is set, then that HTML text or the
#   contents of that named file (respectively) will be inserted into any HTML
#   page retrieved through this proxy.  $INSERT_HTML takes precedence over
#   $INSERT_FILE.
# When viewing a page with frames, a new top frame is created and the
#   insertions go there.
# NOTE:  Any HTML you insert should not have relative URLs in it!  The problem
#   is that there is no appropriate base URL to resolve them with.  So only use
#   absolute URLs in your insertion.  (If you use relative URLs anyway, then
#   a) if $ANONYMIZE_INSERTION is set, they'll be resolved relative to this
#   script's URL, which isn't great, or b) if $ANONYMIZE_INSERTION==0,
#   they'll be unchanged and the browser will simply resolve them relative
#   to the current page, which is usually worse.)
# The frame handling means that it's fairly easy for a surfer to bypass this
#   insertion, by pretending in effect to be in a frame.  There's not much we
#   can do about that, since a page is retrieved the same way regardless of
#   whether it's in a frame.  This script uses a parameter in the URL to
#   communicate to itself between calls, but the user can merely change that
#   URL to make the script think it's retrieving a page for a frame.  Also,
#   many browsers let the user expand a frame's contents into a full window.
# [The warning in earlier versions about setting $INSERT_HTML to '' when using
#   mod_perl and $INSERT_FILE no longer applies.  It's all handled elsewhere.]
# As with $INSERT_ENTRY_FORM, note that any insertion may throw off any
#   precise layout, and the insertion is subject to background colors and
#   other page-wide settings.

#$INSERT_HTML= "<h1>This is an inserted header</h1><hr>" ;
#$INSERT_FILE= 'insert_file_name' ;


# If your insertion has links that you want anonymized along with the rest
#   of the downloaded HTML, then set this to 1.  Otherwise leave it at 0.
$ANONYMIZE_INSERTION= 0 ;

# If there's both a URL entry form and an insertion via $INSERT_HTML or
#   $INSERT_FILE on the same page, the entry form normally goes at the top.
#   Set this to put it after the other insertion.
$FORM_AFTER_INSERTION= 0 ;


# If the insertion is put in a top frame, then this is how many pixels high
#   the frame is.  If the default of 80 or 50 pixels is too big or too small
#   for your insertion, change this.  You can use percentage of screen height
#   if you prefer, e.g. "20%".  (Unfortunately, you can't just tell the
#   browser to "make it as high as it needs to be", but at least the frame
#   will be resizable by the user.)
# This affects insertions by $INSERT_ENTRY_FORM, $INSERT_HTML, and $INSERT_FILE.
# The default here usually works for the inserted entry form, which varies in
#   size depending on $ALLOW_USER_CONFIG.  It also varies by browser.
$INSERTION_FRAME_HEIGHT= $ALLOW_USER_CONFIG   ? 80   : 50 ;



# NOTE THAT YOU SHOULD BE RUNNING CGIPROXY ON A SECURE SERVER!
# Note also that the meaning of '' has changed-- now, all ports except 80
#   are assumed to be using SSL.
# Set this to 1 if the script is running on an SSL server, i.e. it is
#   accessed through a URL starting with "https:"; set this to 0 if it's not
#   running on an SSL server.  This is needed to know how to route URLs back
#   through the proxy.  Regrettably, standard CGI does not yet provide a way
#   for scripts to determine this without help.
# If this variable is set to '' or left undefined, then the program will
#   guess:  SSL is assumed if SERVER_PORT is not 80.  This fails when using
#   an insecure server on a port other than 80, or (less commonly) an SSL server
#   uses port 80, but usually it works.  Besides being a good default, it lets
#   you install the script where both a secure server and a non-secure server
#   will serve it, and it will work correctly through either server.
# This has nothing to do with retrieving pages that are on SSL servers.
$RUNNING_ON_SSL_SERVER= '' ;


# If your server doesn't support NPH scripts, then set this variable to true
#   and try running the script as a normal non-NPH script.  HOWEVER, this
#   won't work as well as running it as NPH; there may be bugs, maybe some
#   privacy holes, and results may not be consistent.  It's a hack.
# Try to install the script as NPH before you use this option, because
#   this may not work.  NPH is supported on almost all servers, and it's
#   usually very easy to install a script as NPH (on Apache, for example,
#   you just need to name the script something starting with "nph-").
# One example of a problem is that Location: headers may get messed up,
#   because they mean different things in an NPH and a non-NPH script.
#   You have been warned.
# For this to work, your server MUST support the "Status:" CGI response
#   header.
$NOT_RUNNING_AS_NPH= 1 ;


# Set HTTP and SSL proxies if needed.  Also see $USE_PASSIVE_FTP_MODE below.
# The format of the first two variables is "host:port", with the port being
#   optional. The format of $NO_PROXY is a comma-separated list of hostnames
#   or domains:  any request for a hostname that ends in one of the strings in
#   $NO_PROXY will not use the HTTP or SSL proxy; e.g. use ".mycompany.com" to
#   avoid using the proxies to access any host in the mycompany.com domain.
# The environment variables in the examples below are appropriate defaults,
#   if they are available.  Note that earlier versions of this script used
#   the environment variables directly, instead of the $HTTP_PROXY and
#   $NO_PROXY variables we use now.
# Sometimes you can use the same proxy (like Squid) for both SSL and normal
#   HTTP, in which case $HTTP_PROXY and $SSL_PROXY will be the same.
# $NO_PROXY applies to both SSL and normal HTTP proxying, which is usually
#   appropriate.  If there's demand to differentiate those, it wouldn't be
#   hard to make a separate $SSL_NO_PROXY option.
#$HTTP_PROXY= $ENV{'http_proxy'} ;
#$SSL_PROXY= 'firewall.example.com:3128' ;
#$NO_PROXY= $ENV{'no_proxy'} ;


# If your HTTP and SSL proxies require authentication, this script supports
#   that in a limited way: you can have a single username/password pair per
#   proxy to authenticate with, regardless of realm.  In other words, multiple
#   realms aren't supported for proxy authentication (though they are for
#   normal server authentication, elsewhere).
# Set $PROXY_AUTH and $SSL_PROXY_AUTH either in the form of "username:password",
#   or to the actual base64 string that gets sent in the Proxy-Authorization:
#   header.  Often the two variables will be the same, when the same proxy is
#   used for both SSL and normal HTTP.
#$PROXY_AUTH= 'Aladdin:open sesame' ;
#$SSL_PROXY_AUTH= $PROXY_AUTH ;


# This is one way to handle pages that don't work well, by redirecting to other working
#   versions of the pages (for example, to a mobile version or another version that
#   doesn't have much JavaScript).  How it works:  If the current domain matches one
#   of the keys of %REDIRECTS, then s/// (string substitution) is done on the URL,
#   using the match and replacement patterns in the 2-element value array.
# The set of sites handled this way is Facebook and Gmail, since they doesn't
#   always work well, or are slow, through CGIProxy.  If you want to access
#   them normally, then comment out or remove the line(s) below for that site.
# If you want to redirect more sites, you can add records to the %REDIRECTS
#   hash in the following way:  Set the hash key to the name of the server you
#   want to redirect, and the value to a reference to a 2-element array containing
#   the left and right sides of an s/// string substitution.  If that doesn't make
#   sense, then try to emulate an example below.
%REDIRECTS= (
	     'www.facebook.com' => [qr#^https?://www\.facebook\.com#i, 'https://m.facebook.com'],
	     'mail.google.com' => [qr#^https?://mail\.google\.com/.*shva=\w*1.*$#i, 'https://mail.google.com/?ui=html']
	    ) ;
							    

# Here's an experimental feature that may or may not be useful.  It's trivial
#   to add, so I added it.  It was inspired in part by Mike Reiter's and Avi
#   Rubin's "Crowds", at http://www.research.att.com/projects/crowds/ .
#   Let me know if you find a use for it.
# The idea is that you have a number of mutually-trusting, cooperating
#   proxies that you list in @PROXY_GROUP().  If that is set, then instead
#   of rerouting all URLs back through this proxy, the script will choose
#   one of these proxies at random to reroute all URLs through, for each
#   run.  This could be used to balance the load among several proxies, for
#   example.  Under certain conditions it could conceivably help privacy by
#   making it harder to track a user's session, but under certain other
#   conditions it could make it easier, depending on how many people,
#   proxies, and proxy servers are involved.  For each page, both its
#   included images and followed links will go through the same proxy, so a
#   clever target server could determine which proxy servers are in each
#   group.
# proxy_encode() and proxy_decode() must be the same for all proxies in the
#   group.  Same goes for pack_flags() and unpack_flags() if you modified them,
#   and probably certain other routines and configuration options.
# Cookies and Basic authentication can't be supported with this, sorry, since
#   cookies can only be sent back to the proxy that created them.
# Set this to a list of absolute URLs of proxies, ending with "nph-proxy.cgi"
#   (or whatever you named the script).  Be sure to include the URL of this
#   proxy, or it will never redirect back through here.  Each proxy in the
#   group should have the same @PROXY_GROUP.
# Alternately, you could set each proxy's @PROXY_GROUP differently for more
#   creative configuration, such as to balance the load unevenly, or to send
#   users through a "round-robin" cycle of proxies.

#@PROXY_GROUP= ('http://www.example.com/~grommit/proxy/nph-proxy.cgi',
#	        'http://www.fnord.mil/langley/bavaria/atlantis/nph-proxy.cgi',
#	        'http://www.nothinghere.gov/No/Such/Agency/nph-proxy.cgi',
#	        ) ;


# Normally, your browser stores all pages you download in your computer's
#   hard drive and memory, in the "cache".  This saves a lot of time and
#   bandwidth the next time you view the page (especially with images, which
#   are bigger and may be shared among several pages).  However, in some
#   situations you may not want the pages you've visited to be stored.  If
#   $MINIMIZE_CACHING is set, then this proxy will try its best to prevent any
#   caching of anything retrieved through it.
# NOTE:  This cannot guarantee that no caching will happen.  All we can do is
#   instruct the browser not to cache anything.  A faulty or malicious browser
#   could cache things anyway if it chose to.
# NOTE:  This has nothing to do with your browser's "history list", which may
#   also store a list of URLs you've visited.
# NOTE:  If you use this, you will use a lot more bandwidth than without it,
#   and pages will seemingly load slower, because if a browser can't cache
#   anything locally then it has to load everything across the network every
#   time it needs something.
$MINIMIZE_CACHING= 0 ;


# Normally, each cookie includes an expiration time/date, and the cookie stays
#   in effect until then, even after you exit your browser and restart it
#   (which normally means the cookie is stored on the hard drive).  Any cookie
#   that has no explicit expiration date is a "session cookie", and stays in
#   effect only as long as the browser is running, and presumably is forgotten
#   after that.  If you set $SESSION_COOKIES_ONLY=1, then *all* cookies that
#   pass through this proxy will be changed to session cookies.  This is useful
#   at a public terminal, or wherever you don't want your cookies to remain
#   after you exit the browser.
# NOTE:  The clock on the server where this runs must be correct for this
#   option to work right!  It doesn't have to be exact, but don't have it off
#   by hours or anything like that.  The problem is that we must not alter any
#   cookies set to expire in the past, because that's how sites delete cookies.
#   If a cookie is being deleted, we DON'T want to turn it into a session
#   cookie.  So this script will not alter any cookies set to expire before the
#   current time according to the system clock.
$SESSION_COOKIES_ONLY= 0 ;


# Cookies have a URL path associated with them; it determines which URLs on a
#   server will receive the cookie in requests.  If the path is not specified
#   when the cookie is created, then the path is supposed to default to the
#   path of the URL that the cookie was retrieved with, according to the
#   cookie specification from Netscape.  Unfortunately, most browsers seem
#   to ignore the spec and instead give cookies a default path of "/", i.e.
#   "send this cookie with all requests to this server".  So, *sigh*, this
#   script uses "/" as the default path also.  If you want this script to
#   follow the specification instead, then set this variable to true.
$COOKIE_PATH_FOLLOWS_SPEC= 0 ;


# Technically, cookies must have a domain containing at least two dots if the
#   TLD is one of the main non-national TLD's (.com, .net, etc.), and three
#   dots otherwise.  This is to prevent malicious servers from setting cookies
#   for e.g. the entire ".co.uk" domain.  Unfortunately, this prescribed
#   behavior does not accommodate domains like ".google.de".  Thus, browsers
#   seem to not require three dots, and thus, this script will do the same by
#   default.  Set $RESPECT_THREE_DOT_RULE if you want the strictly correct
#   behavior instead.
$RESPECT_THREE_DOT_RULE= 0 ;


# Set $USER_AGENT to something generic like this if you want to be extra
#   careful.  Conceivably, revealing which browser you're using may be a
#   slight privacy or security risk.
# However, note that some URLs serve different pages depending on which
#   browser you're using, so some pages will change if you set this.
# This defaults to the user's HTTP_USER_AGENT.
#$USER_AGENT= 'Mozilla/4.05 [en] (X11; I; Linux 2.0.34 i586)' ;


# FTP transfers can happen in either passive or non-passive mode.  Passive
#   mode works better if the client (this script) is behind a firewall.  Some
#   people consider passive mode to be more secure, too.  But in certain
#   network configurations, if this script has trouble connecting to FTP
#   servers, you can turn this off to try non-passive mode.
# See http://cr.yp.to/ftp/security.html for a discussion of security issues
#   regarding passive and non-passive FTP.
$USE_PASSIVE_FTP_MODE= 1 ;


# Unlike a normal browser which can keep an FTP session open between requests,
#   this script must make a new connection with each request.  Thus, the
#   FTP welcome message (e.g. the README file) will be received every time;
#   there's no way for this script to know if you've been here before.  Set
#   $SHOW_FTP_WELCOME to true to always show the welcome message, or false
#   to never show it.
$SHOW_FTP_WELCOME= 1 ;


# If set, then modify script content (like JavaScript) as well as possible
#   such that network accesses go through this proxy script.  If not set, then
#   allow script content to pass unmodified, assuming it's not being removed.
# Currently, JavaScript is the only script content that's proxified.
# If this is set, and if you modify proxy_encode() and proxy_decode(), then
#   you MUST modify the JavaScript routines in $ENCODE_DECODE_BLOCK_IN_JS also.
# NOTE:  This proxification of script content may not be perfect.  It's pretty
#   good, but it may be possible to construct malicious JavaScript that reveals
#   your identity to the server.  The purpose of this feature is more to allow
#   scripts to function through the proxy, than to provide bulletproof
#   anonymity.
# The best advice remains:  FOR BEST ANONYMITY, BROWSE WITH SCRIPTS TURNED OFF.
$PROXIFY_SCRIPTS= 1 ;


# If set, then modify ShockWave Flash resources as well as possible such that
#   network accesses go through this proxy script.  If not set, then allow
#   SWF resources to pass unmodified.
# NOTE:  This is still experimental, and the modified SWF apps are sometimes
#   much slower than the unproxified SWF apps.  If this is turned on, then
#   Web pages with SWF may run much more slowly and possibly bog down
#   your browser, even if the rest of the page is fast.  Remember that SWF
#   apps are pretty common in ads and other places in the page that we tend
#   to ignore.
$PROXIFY_SWF= 1 ;


# To support video in Flash 9+, this program spawns a specialized RTMP proxy
#   daemon that listens on a port (1935 if possible) and dies after 10 minutes
#   of no connections.  This is useful, but some sysadmins may not like it.
#   If you want to prevent the daemon, set $ALLOW_RTMP_PROXY=0 .  Note that
#   Flash 9+ video won't always work if you do so.
# As of release 2.1, the RTMP proxy isn't used yet, so turn it off.
$ALLOW_RTMP_PROXY= 0 ;


# Though JavaScript is by far the most common kind of script, there are other
#   kinds too, such as Microsoft's VBScript.  This program proxifies JavaScript
#   content, but not other script content, which means those other scripts
#   could open privacy holes.  Thus, the default behavior of this program is
#   to remove those other scripts.  Set this variable to true if you'd rather
#   let those scripts through.
# How this works with $REMOVE_SCRIPTS and the "remove scripts" user checkbox:
#   If $ALLOW_UNPROXIFIED_SCRIPTS is false, then unsupported scripts will
#   always be removed.  If it is true, then it is subject to those other
#   settings, just like supported script types are.
# For now, this also controls whether unproxified SWF (Flash) apps are allowed
#   through the proxy.  This means that by default, SWF apps are removed
#   from pages.  This is the safest, but may leave some pages looking
#   incomplete.  If you want to display SWF apps, then you need to set either
#   $PROXIFY_SWF or $ALLOW_UNPROXIFIED_SCRIPTS .  This arrangement can change
#   if there is demand.
$ALLOW_UNPROXIFIED_SCRIPTS= 0 ;


# Comments may contain HTML in them, which shouldn't be rendered but may be
#   relevant in some other way.  Set this flag if you want the contents of
#   comments to be proxified like the rest of the page, i.e. proxify URLs,
#   stylesheets, scripts, etc.
$PROXIFY_COMMENTS= 0 ;


# Apparently, some censoring filters search outgoing request URIs, but not
#   POST request bodies.  Set this to make the initial input form submit
#   using POST instead of GET.
$USE_POST_ON_START= 1 ;


# If this is set, then the URL the user enters in the start form or the top
#   form will be encoded by _proxy_jslib_proxy_encode() before it's submitted.
#   This can keep the URL the user visits private.
# Note that if you set this, you need to modify proxy_encode() above (along
#   with proxy_decode() and the two analogous JavaScript routines) if you
#   want the URL to actually be encoded to something non-obvious.
$ENCODE_URL_INPUT= 1 ;


# Apparently, some censoring filters look at titles on HTML pages.  Set this
#   to remove HTML page titles.
# Note that this does NOT remove titles that are generated by script content,
#   since those would have no effect on a filter.
$REMOVE_TITLES= 0 ;


# If set, this option prevents a user from calling the proxy through the
#   proxy itself, i.e. looping.  It's normally a mistake on the user's part,
#   and a waste of resources.
# This isn't foolproof; it just catches the obvious mistakes.  It's probably
#   pretty easy for a malicious user to make the script call itself, or s/he
#   can always use two proxies to call each other in a loop.  This doesn't
#   account for IP addresses or multiple hostnames for the same server.
$NO_BROWSE_THROUGH_SELF= 0 ;


# Set this to leave out the "Restart" link at the bottom of error pages, etc.
# In some situations this could make it harder for search engines to find the
#   start page.
$NO_LINK_TO_START= 0 ;


# For the obscure case when a POST must be repeated because of user
#   authentication, this is the max size of the request body that this
#   script will store locally.  If CONTENT_LENGTH is bigger than this,
#   the body's not saved at all-- the first POST will be correct, but
#   the second will not happen at all (since a partial POST is worse than
#   nothing).
$MAX_REQUEST_SIZE= 4194304 ;  # that's 4 Meg to you and me



# When handling HTML resources, CGIProxy downloads the entire resource before
#   modifying it and returning it to the client.  However, some operations
#   (such as time-intensive queries) return the first part of a page while
#   still generating the last part.  On such pages, the user might like to
#   see that first part without waiting for the entire response, which they
#   would normally have to do when using CGIProxy.  So, if this option is set,
#   then CGIProxy will return proxified HTML parts as soon as it receives them
#   from the server.  This is less efficient; for example, it means that every
#   page will have the JavaScript library inserted, even if it's not needed
#   (though that wouldn't be too bad since the library is normally cached
#   anyway).  So, we want to do this only for certain pages and not for all.
#   Thus, set this to a list of patterns that match URLs you want to handle
#   this way.  The patterns work like @ALLOWED_SERVERS and @BANNED_SERVERS
#   above, in that they're lists of Perl 5 regular expressions.  See the
#   comments there for details.
# The sample webfeat.org pattern is appropriate for libraries who use the
#   WebFeat service.
#@TRANSMIT_HTML_IN_PARTS_URLS= (
#    '^https?://search3\.webfeat\.org/cgi-bin/WebFeat\.dll',
#    ) ;



# Normally, if a user tries to access a banned server or use an unsupported
#   scheme (protocol), this script will alert the user with a warning page, and
#   either allow the user to click through to the URL unprotected (i.e. without
#   using the proxy), or ban access altogether.  However, in some VPN-like
#   installations, it may more desirable to let users follow links from
#   protected pages (e.g. within an intranet) that lead to unprotected,
#   unproxified pages (e.g. pages outside of the intranet), with no breaks in
#   the browsing experience.  (This example assumes the proxy owner intends it
#   to be used for browsing only the intranet and not the Internet at large.)
#   Set $QUIETLY_EXIT_PROXY_SESSION to skip any warning message and let the
#   user surf directly to unproxified pages from proxified pages.  Note that
#   this somewhat changes the meaning of @ALLOWED_SERVERS and @BANNED_SERVERS--
#   they're not allowed or banned per se, it's just whether this proxy is
#   willing to handle their traffic.  @BANNED_NETWORKS is unaffected, however,
#   since the IP ranges it contains often make no sense outside of the LAN.
# WARNING:  DO *NOT* SET THIS FLAG IF ANONYMITY IS IMPORTANT AT ALL!!!  IT IS
#   NOT MEANT FOR THAT KIND OF INSTALLATION.  IF THIS IS SET, THEN USERS WILL
#   SURF INTO UNPROXIFIED, UNANONYMIZED PAGES WITH NO WARNING, AND THEIR
#   PRIVACY WILL BE COMPROMISED; THEY MAY NOT EVEN NOTICE FOR A LONG TIME.
#   THIS IS EXACTLY WHAT ANONYMIZING PROXIES ARE CREATED TO AVOID.

$QUIETLY_EXIT_PROXY_SESSION= 0 ;



# WARNING:
# EXCEPT UNDER RARE CIRCUMSTANCES, ANY PROXY WHICH HANDLES SSL REQUESTS
#   SHOULD *ONLY* RUN ON AN SSL SERVER!!!  OTHERWISE, YOU'RE RETRIEVING
#   PROTECTED PAGES BUT SENDING THEM BACK TO THE USER UNPROTECTED.  THIS
#   COULD EXPOSE ANY INFORMATION IN THOSE PAGES, OR ANY INFORMATION THE
#   USER SUBMITS TO A SECURE SERVER.  THIS COULD HAVE SERIOUS CONSEQUENCES,
#   EVEN LEGAL CONSEQUENCES.  IT UNDERMINES THE WHOLE PURPOSE OF SECURE
#   SERVERS.
# THE *ONLY* EXCEPTION IS WHEN YOU HAVE *COMPLETE* TRUST OF THE LINK
#   BETWEEN THE BROWSER AND THE SERVER THAT RUNS THE SSL-HANDLING PROXY,
#   SUCH AS ON A CLOSED LAN, OR IF THE PROXY RUNS ON THE SAME MACHINE AS
#   THE BROWSER.
# IF YOU ARE ABSOLUTELY SURE THAT YOU TRUST THE USER-TO-PROXY LINK, YOU
#   CAN OVERRIDE THE AUTOMATIC SECURITY MEASURE BY SETTING THE FLAG BELOW.
#   CONSIDER THE CONSEQUENCES VERY CAREFULLY BEFORE YOU RUN THIS SSL-ACCESSING
#   PROXY ON AN INSECURE SERVER!!!

$OVERRIDE_SECURITY= 1 ;



# Stuff below here you probably shouldn't modify unless you're messing with
#   the code.


# This lists all MIME types that could identify a script, and which will be
#   filtered out as well as possible if removing scripts:  HTTP responses with
#   Content-Type: set to one of these will be nixed, certain HTML which links
#   to one of these types will be removed, style sheets with a type here will
#   be removed, and other odds and ends.
# These are used in matching, so can't contain special regex characters.
# This list is also used for the the $PROXIFY_SCRIPTS function.
# This list contains all script MIME types I know of, but I can't guarantee
#   it's a complete list.  It's largely taken from the examples at
#     http://www.robinlionheart.com/stds/html4/scripts.html
#   That page describes only the first four below as valid.
# The page at ftp://ftp.isi.edu/in-notes/iana/assignments/media-types/media-types
#   lists all media (MIME) types registered with the IANA, but unfortunately
#   many script types (especially proprietary ones) have not registered with
#   them, and that list doesn't specify which types are script content anyway.
@SCRIPT_MIME_TYPES= ('application/x-javascript', 'application/x-ecmascript',
		     'application/x-vbscript',   'application/x-perlscript',
		     'application/javascript',   'application/ecmascript',
		     'text/javascript',  'text/ecmascript', 'text/jscript',
		     'text/livescript',  'text/vbscript',   'text/vbs',
		     'text/perlscript',  'text/tcl',
		     'text/x-scriptlet', 'text/scriptlet',
		     'application/hta',   'application/x-shockwave-flash',
		    ) ;



# All MIME types in @SCRIPT_MIME_TYPES and @OTHER_TYPES_TO_REGISTER will be
#   "registered".  Registration helps the script remember which MIME type is
#   expected by a page when downloading embedded URLs, e.g. style sheets.  Any
#   MIME types that need special treatment should be listed here if they're not
#   already in @SCRIPT_MIME_TYPES.
# If you write a handler for a new MIME type in proxify_block(), and that type
#   isn't already listed in @SCRIPT_MIME_TYPES, then add it here.
# The Perl code in this program supports up to 64 registered MIME types, but
#   the JS _proxy_jslib_pack_flags() and _proxy_jslib_unpack_flags() routines
#   only support 26.  Thus, fix the JS code if there's ever more than 26 types.
# "x-proxy/xhr" is a special case-- it's used to support the JavaScript class
#   XMLHttpRequest .  Data downloaded through that should not be proxified,
#   even if it's HTML data; it's proxified later when it's added to a document.
#   Using the "x-proxy/xhr" type is part of avoiding that first proxification.
@OTHER_TYPES_TO_REGISTER= ('text/css', 'x-proxy/xhr') ;


# These are MIME types that we *may* try to rewrite in proxify_block(), e.g.
#   to send all URLs back through this script.  If a type isn't on this list,
#   then we know for certain it should be sent back to the user unchanged,
#   which saves time.
# If you write a handler for a new MIME type in proxify_block(), then add the
#   type here.
# NOT all the types here are actually supported at this time!
# text/html is not on this list because currently it's handled specially.
@TYPES_TO_HANDLE= ('text/css',
		   'application/x-javascript', 'application/x-ecmascript',
		   'application/javascript',   'application/ecmascript',
		   'text/javascript',          'text/ecmascript',
		   'text/livescript',          'text/jscript',
		   'application/x-shockwave-flash',
		  ) ;


# This is a list of all file extensions that will be disallowed if
#   $TEXT_ONLY is set.  It's an inexact science.  If you want to ban
#   other file extensions, you can add more to this list.  Note that
#   removing extensions from this list won't necessarily allow those
#   files through, since there are other ways $TEXT_ONLY is implemented,
#   such as only allowing MIME types of text/* .
# The format of this list is one long string, with the extensions
#   separated by "|".  This is because the string is actually used as
#   a regular expression.  Don't worry if you don't know what that means.
# Extensions are roughly taken from Netscape's "Helper Preferences" screen
#   (but that was in 1996).  A more complete list might be made from a
#   mime.types file.
$NON_TEXT_EXTENSIONS=
	  'gif|jpeg|jpe|jpg|tiff|tif|png|bmp|xbm'   # images
	. '|mp2|mp3|wav|aif|aiff|au|snd'            # audios
	. '|avi|qt|mov|mpeg|mpg|mpe'                # videos
	. '|gz|Z|exe|gtar|tar|zip|sit|hqx|pdf'      # applications
	. '|ram|rm|ra|swf' ;                        # others



$PROXY_VERSION= '2.1.6' ;


#--------------------------------------------------------------------------
#   End of normal user configuration.
#   Now, set or adjust all globals that remain constant for all runs.
#--------------------------------------------------------------------------

# First, set various constants.

# Convert $RUN_AS_USER to a numeric UID if needed.
no warnings 'numeric' ;
$RUN_AS_USER= getpwnam($RUN_AS_USER)
    if $RUN_METHOD eq 'embedded' and $RUN_AS_USER==0 and $^O!~ /win/i ;
use warnings 'numeric' ;

# Use local::lib if so configured.  Don't use it when installing modules
#   or when purging the database.
if ($LOCAL_LIB_DIR and $ARGV[0] ne 'install-modules' and $ARGV[0] ne 'purge-db') {
    push(@INC, File::Spec->catdir($LOCAL_LIB_DIR, qw(lib perl5))) ;
    eval { require local::lib ; local::lib->import($LOCAL_LIB_DIR) } ;  # ignore errors
}

# Allow installer to set $DB_DRIVER="MySQL" in config.
$DB_DRIVER= 'mysql' if lc($DB_DRIVER) eq 'mysql' ;


# These are used in rfc1123_date() and date_is_after().
@MONTH=   qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec) ;
@WEEKDAY= qw(Sun Mon Tue Wed Thu Fri Sat Sun) ;
%UN_MONTH= map { lc($MONTH[$_]), $_ }  0..$#MONTH ;   # look up by month name

# Create the sets of regular expressions we'll need if we proxify scripts.
# So far, the only script type we proxify is JavaScript.
&set_RE_JS  if $PROXIFY_SCRIPTS ;


# Next, make copies of any constant environment variables, and fix as needed.

# SERVER_PORT and SCRIPT_NAME will be constant, and are used in several places.
#   Besides, we need SCRIPT_NAME fixed before setting $THIS_SCRIPT_URL.
# SCRIPT_NAME should have a leading slash, but the old CGI "standard" from
#   NCSA was unclear on that, so some servers didn't give it a leading
#   slash.  Here we ensure it has a leading slash.
# Exception:  If SCRIPT_NAME is empty, then we're using a daemon, so leave it empty.
# Apache has a bug where SCRIPT_NAME is wrong if the PATH_INFO has "//" in it;
#   it's set to the script name plus all of PATH_INFO up until its final "//".
#   To work around this, truncate SCRIPT_NAME at the first place it matches $0.
#   PATH_INFO is also changed to collapse all multiple slashes into a single
#   slash, which is not worked around here.  This bug should be fixed in
#   Apache 2.0.55 and later.
# Some servers provide $0 as a complete path rather than just the filename,
#   so extract the filename.
$ENV{SCRIPT_NAME}=~ s#^/?#/#  if $ENV{SCRIPT_NAME} ne '' ;
if ($ENV{SERVER_SOFTWARE}=~ /^Apache\b/i) {
    my($zero)= $0=~ m#([^/]*)$# ;
    ($ENV{SCRIPT_NAME})= $ENV{SCRIPT_NAME}=~ /^(.*?\Q$zero\E)/ if $zero ne '' ;
}
$ENV_SERVER_PORT= $ENV{SERVER_PORT} ;
$ENV_SCRIPT_NAME= $ENV{SCRIPT_NAME} ;

# The nginx server sets SCRIPT_NAME to the entire request-URI, so fix it.
# Must do this only on $ENV_SCRIPT_NAME and not $ENV{SCRIPT_NAME}, because
#   later we'll need the latter to get PATH_INFO.  :P
if ($ENV{SERVER_SOFTWARE}=~ /^nginx\b/i) {
    if ($RUN_METHOD eq 'fastcgi') {
	$ENV_SCRIPT_NAME= '/' . $SECRET_PATH ;
    } else {
	my($zero)= $0=~ m#([^/]*)$# ;
	($ENV_SCRIPT_NAME)= $ENV_SCRIPT_NAME=~ /^(.*?\Q$zero\E)/  if $zero ne '' ;
    }
}

# If we're running as the embedded server, use $SECRET_PATH .
$ENV_SCRIPT_NAME= '/' . $SECRET_PATH  if $RUN_METHOD eq 'embedded' ;

# Next, adjust config variables as needed, or create any needed constants from
#   them.

# Create @BANNED_NETWORK_ADDRS from @BANNED_NETWORKS.
# No error checking; assumes the proxy owner set @BANNED_NETWORKS correctly.
@BANNED_NETWORK_ADDRS= () ;
for (@BANNED_NETWORKS) {
    push(@BANNED_NETWORK_ADDRS, pack('C*', /(\d+)/g)) ;
}


# For the external tests, create hashes of parsed URLs if the tests are CGI calls.
# Note that the socket names must each be unique!
@{$USER_IP_ADDRESS_TEST_H}{qw(host port path socket open)}=
	(lc($1), ($2 eq '' ? 80 : $2), $3, 'S_USERTEST', 0)
    if ($USER_IP_ADDRESS_TEST=~ m#http://([^/?:]*):?(\d*)(.*)#i) ;
@{$DESTINATION_SERVER_TEST_H}{qw(host port path socket open)}=
	(lc($1), ($2 eq '' ? 80 : $2), $3, 'S_DESTTEST', 0)
    if ($DESTINATION_SERVER_TEST=~ m#http://([^/?:]*):?(\d*)(.*)#i) ;


# Require a full path in $PROXY_DIR.
# Currently only used when using embedded server, but that may change.
# Use different patterns for Windows vs. everything else.
die "Must use full directory path in \$PROXY_DIR setting; currently set to \"$PROXY_DIR\".\n"
    if $RUN_METHOD eq 'embedded' and $PROXY_DIR!~ ($^O=~ /win/i  ? qr#^([a-zA-Z]:)?[/\\]#  : qr#^/#) ;


# If $RUNNING_ON_SSL_SERVER is '', then guess based on SERVER_PORT.
$RUNNING_ON_SSL_SERVER= ($ENV_SERVER_PORT!=80) if $RUNNING_ON_SSL_SERVER eq '' ;

# Or, if we're a daemon, then it's always true.
$RUNNING_ON_SSL_SERVER= 1  if $RUN_METHOD eq 'embedded' ;


# $DB_DRIVER is required for $USE_DB_FOR_COOKIES to be true.
$USE_DB_FOR_COOKIES= 0  unless $DB_DRIVER ne '' ;


# Set this constant based on whether the server is IIS, because we have to
#   test it later for every run to work around a bug in IIS.  A constant here
#   saves time when using mod_perl.
$RUNNING_ON_IIS= ($ENV{'SERVER_SOFTWARE'}=~ /IIS/) ;


# FastCGI doesn't support NPH scripts.  :P
$NOT_RUNNING_AS_NPH= 1  if $RUN_METHOD eq 'fastcgi' ;


# Create @NO_PROXY from $NO_PROXY for efficiency.
@NO_PROXY= split(/\s*,\s*/, $NO_PROXY) ;


# Base64-encode $PROXY_AUTH and $SSL_PROXY_AUTH if they're not encoded already.
$PROXY_AUTH=     &base64($PROXY_AUTH)      if $PROXY_AUTH=~ /:/ ;
$SSL_PROXY_AUTH= &base64($SSL_PROXY_AUTH)  if $SSL_PROXY_AUTH=~ /:/ ;


# Guarantee URLs in @PROXY_GROUP have no trailing slash.
foreach (@PROXY_GROUP) { s#/$## }


# Create $NO_CACHE_HEADERS depending on $MINIMIZE_CACHING setting; it is placed
#   in every response.  Note that in all the "here documents" we use for error
#   messages, it has to go on the same line as another header to avoid a blank
#   line in the response.
$NO_CACHE_HEADERS= $MINIMIZE_CACHING
    ? "Cache-Control: no-cache\015\012Pragma: no-cache\015\012"
    : '' ;


# Canonicalize all MIME types to lowercase.
for (@SCRIPT_MIME_TYPES)        { $_= lc }
for (@OTHER_TYPES_TO_REGISTER)  { $_= lc }

# Create @ALL_TYPES and %MIME_TYPE_ID, which are inverses of each other.
# This is useful e.g. to identify the MIME type expected in a given download,
#   in a one-character flag.  That's why we limit this to 64 types for now.
# $ALL_TYPES[0] is '', so we can test e.g. "if $MIME_TYPE_ID{$id} ..." .

@ALL_TYPES= ('', @SCRIPT_MIME_TYPES, @OTHER_TYPES_TO_REGISTER) ;
&HTMLdie("Too many MIME types to register.")  if @ALL_TYPES > 64 ;
@MIME_TYPE_ID{@ALL_TYPES}=  0..$#ALL_TYPES ;


# Regex that matches a script MIME type.
$SCRIPT_TYPE_REGEX= '(' . join("|", @SCRIPT_MIME_TYPES) . ')' ;

# Regex that tells us whether we handle a given MIME type.
$TYPES_TO_HANDLE_REGEX= '(' . join("|", @TYPES_TO_HANDLE) . ')' ;


# Only need to run this routine once
$HAS_INITED= 1 ;


# End of initialization of constants.

}  # sub init {


#--------------------------------------------------------------------------
#   Global constants are now set.  Now do any initialization that is
#     required for every run.
#--------------------------------------------------------------------------

# What used to be the "main" code has now been divided up between init() and
#   one_run() .
sub one_run {

# OK, let's time this thing
#my $starttime= time ;
#my($sutime,$sstime)= (times)[0,1] ;


# This is needed to run an NPH script under mod_perl.
# Other stuff needed for mod_perl:
#   must use at least Perl 5.004, or STDIN and STDOUT won't behave correctly;
#   cannot use exit();
#   must initialize or reset all vars;
#   regex's with /o option retain state between calls, so be careful;
#   typeglobbing of *STDIN doesn't work, so must pass filehandles as strings.
local($|)= 1 ;

# In mod_perl, global variables are retained between calls, so they must
#   be initialized correctly.  In this program, (most) UPPER_CASE variables
#   are persistent constants, i.e. they aren't changed after they're 
#   initialized above (in the $HAS_BEGUN block).  We also assume that no
#   lower_case variables are set before here.  It's a little hacky and possibly
#   error-prone if user customizations don't follow these conventions, but it's
#   fast and simple.
# So, if you're using mod_perl and you make changes to this script, don't
#   modify existing UPPER_CASE variables after the $HAS_BEGUN block above,
#   don't set lower_case variables before here, and don't use UPPER_CASE
#   variables for anything that will vary from run to run.
reset 'a-z' ;
$URL= '' ;     # (almost) only uppercase variable that varies from run to run



# Store $now rather than calling time() multiple times.
$now= time ;    # for (@goodmen)


# Set $THIS_HOST to the best guess how this script was called-- use the
#   Host: request header if available; otherwise, use SERVER_NAME.
# We don't bother with a $THIS_PORT, since it's more reliably set to the port
#   through which the script was called.  SERVER_NAME is much more likely to
#   be different from the hostname that the user sees, since one server may
#   handle many domains or have many hostnames.
# This has to be calculated every run, since there may be multiple hostnames.
if ($ENV{'HTTP_HOST'} ne '') {
    ($THIS_HOST)= $ENV{'HTTP_HOST'}=~ m#^(?:[\w+.-]+://)?([^:/?]*)# ;
    $THIS_HOST= $ENV{'SERVER_NAME'}   if $THIS_HOST eq '' ;
} else {
    $THIS_HOST= $ENV{'SERVER_NAME'} ;
}


# Build the constant $THIS_SCRIPT_URL from environment variables.  Only include
#   SERVER_PORT if it's not 80 (or 443 for SSL).
$THIS_SCRIPT_URL= $RUNNING_ON_SSL_SERVER
	    ? 'https://' . $THIS_HOST
	      . ($ENV_SERVER_PORT==443  ? ''  : ':' . $ENV_SERVER_PORT)
	      . $ENV_SCRIPT_NAME
	    : 'http://' . $THIS_HOST
	      . ($ENV_SERVER_PORT==80   ? ''  : ':' . $ENV_SERVER_PORT)
	      . $ENV_SCRIPT_NAME ;


# This script uses whatever version of HTTP the client is using.  So far
#   only 1.0 and 1.1 are supported.
($HTTP_VERSION)= $ENV{'SERVER_PROTOCOL'}=~ m#^HTTP/(\d+\.\d+)#i ;
$HTTP_VERSION= '1.0' unless $HTTP_VERSION=~ /^1\.[01]$/ ;


# Hack to support non-NPH installation-- luckily, the format of a
#   non-NPH response is almost exactly the same as an NPH response.
#   The main difference is the first word in the status line-- something
#   like "HTTP/1.x 200 OK" can be simulated with "Status: 200 OK", as
#   long as the server supports the Status: CGI response header.  So,
#   we set that first word to either "HTTP/1.x" or "Status:", and use
#   it for all responses throughout the script.
# NOTE:  This is not the only difference between an NPH and a non-NPH
#   response.  For example, the Location: header has different semantics
#   between the two types of responses.  This hack is only an approximation
#   that we hope works most of the time.  It's better to install the script
#   as an NPH script if possible (which it almost always is).
# Technically, the HTTP version in the response is supposed to be the highest
#   version supported by the server, even though the rest of the response may
#   be in the format of an earlier version.  Unfortunately, CGI scripts do
#   not have access to that value; it's a hole in the CGI standard.
$HTTP_1_X=  $NOT_RUNNING_AS_NPH   ? 'Status:'   : "HTTP/$HTTP_VERSION" ;


# Fix submitted by Alex Freed:  Under some unidentified conditions,
#   instances of nph-proxy.cgi can hang around for many hours and drag the
#   system.  So until we figure out why that is, here's a 10-minute timeout.
#   Please write me with any insight into this, since I can't reproduce the
#   problem.  Under what conditions, on what systems, does it happen?
# 9-9-1999: One theory is that it's a bug in older Apaches, and is fixed by
#   upgrading to Apache 1.3.6 or better.  Julian Haight reports seeing the
#   same problem with other scripts on Apache 1.3.3, and it cleared up when
#   he upgraded to Apache 1.3.6.  Let me know if you can confirm this.
# alarm() is missing on some systems (such as Windows), so use eval{} to
#   avoid failing when alarm() isn't available.
# As of version 2.1:  We now only do this if we're running on Apache that is
#   earlier than version 1.3.6, to allow large downloads for everyone else.

if ($ENV{'SERVER_SOFTWARE'}=~ m#^Apache/(\d+)\.(\d+)(?:\.(\d+))?#i) {
    if (($1<=>1 or $2<=>3 or $3<=>6) < 0) {
	$SIG{'ALRM'} = \&timeexit ;
	eval { alarm(600) } ;     # use where it works, ignore where it doesn't
    }
}

# Exit upon timeout.  If you wish, add code to clean up and log an error.
sub timeexit { goto EXIT }


# Fix any environment variables that the server may have set wrong.
# Note that some constant environment variables are copied to variables above,
#   and fixed there.

# The IIS server doesn't set PATH_INFO correctly-- it sets it to the entire
#   request URI, rather than just the part after the script name.  So fix it
#   here if we're running on IIS.  Thanks to Dave Moscovitz for the info!
$ENV{'PATH_INFO'} =~ s/^$ENV_SCRIPT_NAME//   if $RUNNING_ON_IIS ;

# The nginx server also doesn't set PATH_INFO, or even SCRIPT_NAME, correctly--
#   it sets SCRIPT_NAME to the entire request URI, and PATH_INFO to nothing.  So fix it.
# $ENV_SCRIPT_NAME has earlier been set correctly.
($ENV{PATH_INFO}= $ENV{SCRIPT_NAME})=~ s/^\Q$ENV_SCRIPT_NAME\E//
    if $ENV{SERVER_SOFTWARE}=~ /^nginx\b/i ;

# PATH_INFO may or may not be URL-encoded when we get it; it seems to vary
#   by server.  This script assumes it's still encoded.  Thus, if it's not,
#   we need to re-encode it.
# The only time this seems to come up is when spaces are in URLs, correctly
#   represented in the URL as %20 but decoded to " " in PATH_INFO.  Thus,
#   this hack only focuses on space characters.  It's a hack that I'm not at
#   all comfortable with.  :P
# Very yucky business, this encoding thing.
if ($ENV{'PATH_INFO'}=~ / /) {
    $ENV{'PATH_INFO'} =~ s/%/%25/g ;
    $ENV{'PATH_INFO'} =~ s/ /%20/g ;
}


# Protect with $SECRET_PATH when appropriate.
if ($RUN_METHOD eq 'embedded' and !($ENV{'PATH_INFO'}=~ s#^/\Q$SECRET_PATH\E($|/)#$1#)) {
    select((select($STDOUT), $|=1)[0]) ;    # unbuffer the socket
    print $STDOUT "HTTP/1.1 404 Not Found\015\012\015\012" ;
    die "exiting" ;
}


# Copy often-used environment vars into scalars, for efficiency
$env_accept= $ENV{'HTTP_ACCEPT'} || '*/*' ;     # may be modified later



# PATH_INFO consists of a path segment of flags, followed by the encoded
#   target URL.  For example, PATH_INFO might be something like
#   "/010100A/http/www.example.com".  The actual format of the flag segment
#   is defined in the routine pack_flags().
# Thanks to Mike Harding for the idea of using another flag for the
#   $is_in_frame parameter, instead of using two parallel scripts.

# Extract flags and encoded URL from PATH_INFO.
($packed_flags, $encoded_URL)= $ENV{'PATH_INFO'}=~ m#^/([^/]*)/?(.*)# ;

# Set all $e_xxx variables ("effective-xxx") and anything else from flag
#   segment of PATH_INFO.  If user config is not allowed or if flag segment
#   is not present, then set $e_xxx variables from hard-coded config variables
#   instead (but still set anything else as needed from PATH_INFO).
if ( $ALLOW_USER_CONFIG && ($packed_flags ne '') ) {
    ($e_remove_cookies, $e_remove_scripts, $e_filter_ads, $e_hide_referer,
     $e_insert_entry_form, $is_in_frame, $expected_type)=
	 &unpack_flags($packed_flags) ;

} else {
    # $is_in_frame is set in any case.  It indicates whether the current
    #   request will be placed in a frame.
    ($e_remove_cookies, $e_remove_scripts, $e_filter_ads, $e_hide_referer,
     $e_insert_entry_form, $is_in_frame, $expected_type)=
	 ($REMOVE_COOKIES, $REMOVE_SCRIPTS, $FILTER_ADS, $HIDE_REFERER,
	  $INSERT_ENTRY_FORM, (&unpack_flags($packed_flags))[5..6] ) ;
}

# Set any other $e_xxx variables not from flag segment [none currently].



# Flags are now set, and $encoded_URL now contains only the encoded target URL.



# Create a one-flag test for whether we're inserting anything into THIS page.
# This must happen after user flags are read, just above.
$doing_insert_here= !$is_in_frame && 
    ( $e_insert_entry_form || ($INSERT_FILE ne '') || ($INSERT_HTML ne '') ) ;


# One user reported problems with binary files on certain other OS's, and
#   this seemed to fix it.  Supposedly, either this or the "binmode S"
#   statements below the newsocketto() calls work, or all; I'm putting all in.
#   Tell me anything new you figure out about this.
binmode $STDOUT ;


#--------------------------------------------------------------------------
#    parse URL, make checks, and set various globals
#--------------------------------------------------------------------------

# Calculate $url_start for use later in &full_url() and elsewhere.  It's an
#   integral part of &full_url(), placed here for speed, similar to the
#   variables set in &fix_base_vars.
# $url_start is the first part of every proxified URL.  A complete proxified
#   URL is made by appending &wrap_proxy_encode(URL) (and possibly a #fragment) to
#   $url_start.  $url_start normally consists of the current script's URL
#   (or one from @PROXY_GROUP), plus a flag segment in PATH_INFO, complete
#   with trailing slash.  For example, a complete $url_start might be
#   "http://www.example.com/path/nph-proxy.cgi/010110A/" .
# $url_start_inframe and $url_start_noframe are used to force the frame flag
#   on or off, for example when proxifying a link that causes frames to be
#   entered or exited.  Otherwise, most links inherit the current frame state.
# $script_url is used later for Referer: support, and whenever a temporary
#   copy of $url_start has to be generated.
# In earlier versions of CGIProxy, $url_start was called $this_url, which is
#   really what it was originally.  Its semantics had drifted somewhat since
#   then, so they have been cleaned up, and $url_start is now more descriptive.

# Set $url_start to a random element of @PROXY_GROUP, if that is set.
if (@PROXY_GROUP) {
    # srand is automatically called in Perl 5.004 and later.  It might be
    #   desirable to seed based on the URL, so that multiple requests for
    #   the same URL go through the same proxy, and may thus be cached.
    #srand( unpack('%32L*', $ENV{'PATH_INFO'}) ) ;  # seed with URL+flags
    $script_url= $PROXY_GROUP[ rand(scalar @PROXY_GROUP) ] ;
} else {
    $script_url= $THIS_SCRIPT_URL ;
}

# Create $url_start and any needed variants: "$script_url/flags/"
$url_start_inframe= $script_url . '/' .
    &pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
		$e_hide_referer, $e_insert_entry_form, 1, '') . '/' ;
$url_start_noframe= $script_url . '/' .
    &pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
		$e_hide_referer, $e_insert_entry_form, 0, '') . '/' ;
$url_start=  $is_in_frame   ? $url_start_inframe   : $url_start_noframe ;


# If there's no $encoded_URL, then start a browsing session.
&show_start_form() if $encoded_URL eq '' ;


# Decode the URL.
$URL= &wrap_proxy_decode($encoded_URL) ;


# Set the query string correctly, from $ENV{QUERY_STRING} and what's already
#   in $URL.
# The query string may exist either within the encoded URL or in the containing
#   URL, as $ENV{QUERY_STRING}.  If the former, then the query string was
#   (definitely?) in a referenced URL, while the latter most likely implies a
#   GET form input.
# With Flash apps adding e.g. "?range=100-1000" to proxified URLs, both
#   query strings may be valid, so append $ENV{'QUERY_STRING'} to the end
#   of the URL appropriately.
# Note that Netscape does not pass any query string data that is part of the
#   URL in the <form action> attribute, which is probably correct behaviour.
#   For this program to act exactly the same, it would need to strip the
#   query string when updating all <form action> URLs, way below.

$URL.= ($URL=~ /\?/  ? '&'  : '?') . $ENV{'QUERY_STRING'}  if $ENV{'QUERY_STRING'} ne '' ;


# Parse the URL, using a regex modelled from the one in RFC 2396 (URI syntax),
#   appendix B.
# This assumes a hierarchical scheme; it won't work for e.g. mailto:
# "authority" is the combination of host, port, and possibly other info.
# Note that $path here will also contain any query component; it's more like
#   the request URI.
# Note that $URL is guaranteed to be an absolute URL with no "#" fragment,
#   though this does little error-checking.  Note also that the old ";"
#   parameters are now included in the path component.

($scheme, $authority, $path)= ($URL=~ m#^([\w+.-]+)://([^/?]*)(.*)$#i) ;
$scheme= lc($scheme) ;
$path= "/$path" if $path!~ m#^/# ;   # if path is '' or contains only query


# If so configured, handle session cookies.
# This all has to be done before calling xproxy() below, because some is
#   used for cookie management.
if ($USE_DB_FOR_COOKIES) {
    # Attempt to get session cookies from HTTP_COOKIE .
    get_session_cookies() ;

    # Now that we're using a database, we need session IDs.  20 random alphanumeric
    #   characters means one collision in roughly 10^18 simultaneous uses.
    # One session ID is itself a session-length cookie, and is used to store
    #   session cookies and anything else we need to expire when the session ends;
    #   the other cookie is persistent, and is used to store all persistent cookies.
    $session_id_persistent= random_string(20) unless $session_id_persistent=~ /^[\dA-Za-z]{20}$/ ;
    my $secure_clause= $RUNNING_ON_SSL_SERVER  ? ' secure;'  : '' ;

    # The persistent session ID lasts one hour after last use (should time be configurable?),
    #   so a Set-Cookie: header will be sent with every response.
    $session_cookies= "Set-Cookie: S2=$session_id_persistent; expires=" . &rfc1123_date($now+3600, 1)
		    . "; domain=$THIS_HOST; path=$ENV_SCRIPT_NAME/;$secure_clause HttpOnly\015\012" ;

    # Create and return non-persistent session cookie, if needed.
    if (!($session_id=~ /^[\dA-Za-z]{20}$/)) {
	$session_id= random_string(20) ;
	$session_cookies.= "Set-Cookie: S=$session_id; "
			 . "domain=$THIS_HOST; path=$ENV_SCRIPT_NAME/;$secure_clause HttpOnly\015\012" ;
    }

    # Set $DBH, creating database if needed.
    connect_to_db() ;

    # Insert or update session records.
    update_session_record($session_id) ;
    update_session_record($session_id_persistent) ;

    # Verify their IP address hasn't changed.
    &HTMLdie("Connecting from wrong IP address.")  unless verify_ip_address($session_id) ;
    &HTMLdie("Connecting from wrong IP address.")  unless verify_ip_address($session_id_persistent) ;

}


# Magic here-- if $URL uses special scheme "x-proxy", immediately call the
#   general-purpose xproxy() routine.
&xproxy($URL) if $scheme eq 'x-proxy' ;


# Set $is_html if $path (minus query) ends in .htm or .html .
# MSIE has a bug (and privacy hole) whereby URLs with QUERY_STRING ending
#   in .htm or .html are mistakenly treated as HTML, and thus could have
#   untranslated links, <script> blocks, etc.  So for those cases, set
#   $is_html=true to make sure we later transform it as necessary.
if ($ENV{'HTTP_USER_AGENT'}=~ /MSIE/) {
    $is_html= 1  if $path=~ /\.html?(\?|$)/i ;
} else {
    $is_html= 1  if $path=~ /^[^?]*\.html?(\?|$)/i ;
}


# Alert the user to unsupported URL, with an intermediate page
&unsupported_warning($URL) unless ($scheme=~ /^(http|https|ftp)$/) ;

# Require a host to be present (for $base_url safety later)
# Testing for a valid hostname is more complex than just /\w/ , but this does
#   what we need here.
&HTMLdie('The target URL cannot contain an empty host name.')
    unless $authority=~ /^\w/ ;


# Parse $authority into $host, $port, and possibly others, depending on
#   which URL scheme is used.
# Since most URL schemes use the simple host:port, make that the default.
#   This may avoid oversight later when other URL schemes are added (though
#   be careful of username/password handling in that block below).
# Note that this does not set $port to a default.  In the interest of
#   encapsulation, the default $port should be set in the routine that
#   implements the protocol (i.e. http_get(), ftp_get(), etc.)

if ($scheme eq 'ftp') {
    # FTP authority can be username:password@host:port, with username,
    #   password, and port all optional.
    # Embedding your username/password in a URL is NOT RECOMMENDED!  Here,
    #   the second clause should almost always be used.
    if ($authority=~ /@/) {
	($username, $password, $host, $port)=
	    $authority=~ /([^:@]*):?([^@]*)@([^:]*):?(.*)/ ;
    } else {
	($username, $password)= ('anonymous', 'not@available.com') ;
	($host, $port)= $authority=~ /^([^:]*):?(.*)$/ ;
    }

# covers HTTP, etc.
} else {
    # Unlikely occurrence of username:password@host:port, but possible.
    #   Implies HTTP Basic authentication.  Not as much a security hole as
    #   doing the same in an FTP URL, above, but still not a great idea.
    if ($authority=~ /@/) {
	($username, $password, $host, $port)=
	    $authority=~ /([^:@]*):?([^@]*)@([^:]*):?(.*)/ ;
    } else {
	($host, $port)= $authority=~ /^([^:]*):?(.*)$/ ;
    }
}

$host= lc($host) ;      # hostnames are case-insensitive
$host=~ s/\.*$//g ;     # removes trailing dots to close a potential exploit


# If so configured, disallow browsing back through the script itself (looping).
# This assumes the script can only be called by an http:// or https:// URL.
# This could check SERVER_NAME in addition to $THIS_HOST, but that might
#   match falsely sometimes.  The way it is should still prevent deep loops.
if ($NO_BROWSE_THROUGH_SELF) {
    # Default $port's not set yet, so hack up an ad hoc version.
    my($port2)=  $port || ( $scheme eq 'https'  ? 443  : 80 ) ;
    &loop_disallowed_die($URL)
	if     ($scheme=~ /^https?/)
	    && ($host=~ /^$THIS_HOST$/i)
	    && ($port2 == $ENV_SERVER_PORT)
	    && ($path=~ /^$ENV_SCRIPT_NAME\b/) ;
}


# Die if the user's IP address is not allowed here.
if ($USER_IP_ADDRESS_TEST) {
    my($ok) ;
    if ($USER_IP_ADDRESS_TEST_H) {
	$ok= &http_get2($USER_IP_ADDRESS_TEST_H,
			$USER_IP_ADDRESS_TEST_H->{path} . $ENV{REMOTE_ADDR}) ;
    } else {
	$ok= `$USER_IP_ADDRESS_TEST $ENV{REMOTE_ADDR}` ;
    }
    &banned_user_die if $ok==0 ;
}


# Die if the target server is not allowed, according to $DESTINATION_SERVER_TEST.
if ($DESTINATION_SERVER_TEST) {
    my($ok) ;
    my($safehost)= $host ;
    if ($DESTINATION_SERVER_TEST_H) {
	$safehost=~ s/(\W)/ '%' . sprintf('%02x', ord($1)) /ge ;
	$ok= &http_get2($DESTINATION_SERVER_TEST_H,
			$DESTINATION_SERVER_TEST_H->{path} . $safehost) ;
    } else {
	$safehost=~ s/\\/\\\\/g ;
	$safehost=~ s/'/\\'/g ;
	$ok= `$DESTINATION_SERVER_TEST '$safehost'` ;
    }
    &banned_server_die($URL) if $ok==0 ;
}



# Die if the target server is not allowed, according to @ALLOWED_SERVERS and @BANNED_SERVERS.
if (@ALLOWED_SERVERS) {
    my($server_is_allowed) ;
    foreach (@ALLOWED_SERVERS) {
	$server_is_allowed= 1, last   if $host=~ /$_/ ;
    }
    &banned_server_die($URL) unless $server_is_allowed ;
}
foreach (@BANNED_SERVERS) {
    &banned_server_die($URL) if $host=~ /$_/ ;
}


# If we're filtering ads, set $images_are_banned_here appropriately.
if ($e_filter_ads) {
    foreach (@BANNED_IMAGE_URL_PATTERNS) {
	$images_are_banned_here= 1, last if $URL=~ /$_/ ;
    }
}


# Set $scripts_are_banned_here appropriately
$scripts_are_banned_here= $e_remove_scripts ;
unless ($scripts_are_banned_here) {
    if (@ALLOWED_SCRIPT_SERVERS) {
	$scripts_are_banned_here= 1 ;
	foreach (@ALLOWED_SCRIPT_SERVERS) {
	    $scripts_are_banned_here= 0, last   if $host=~ /$_/ ;
	}
    }
    unless ($scripts_are_banned_here) {
	foreach (@BANNED_SCRIPT_SERVERS) {
	    $scripts_are_banned_here= 1, last   if $host=~ /$_/ ;
	}
    }
}


# Set $cookies_are_banned_here appropriately
$cookies_are_banned_here= $e_remove_cookies ;
unless ($cookies_are_banned_here) {
    if (@ALLOWED_COOKIE_SERVERS) {
	$cookies_are_banned_here= 1 ;
	foreach (@ALLOWED_COOKIE_SERVERS) {
	    $cookies_are_banned_here= 0, last   if $host=~ /$_/ ;
	}
    }
    unless ($cookies_are_banned_here) {
	foreach (@BANNED_COOKIE_SERVERS) {
	    $cookies_are_banned_here= 1, last   if $host=~ /$_/ ;
	}
    }
}


# Disallow the retrieval if the expected MIME type is banned, because some
#   browsers erroneously give the advisory content-type precedence over
#   everything else.
if ($scripts_are_banned_here && $expected_type ne '') {
    &script_content_die if $expected_type=~ /^$SCRIPT_TYPE_REGEX$/io ;
}

# Exclude non-text if it's not allowed.  Err on the side of allowing too much.
if ($TEXT_ONLY) {
    # First, forbid requests for filenames with non-text-type extensions
    &non_text_die if ($path=~ /\.($NON_TEXT_EXTENSIONS)(;|\?|$)/i) ;

    # Then, filter the "Accept:" header to accept only text
    $env_accept=~ s#\*/\*#text/*#g ;    # not strictly perfect
    $env_accept= join(', ', grep(m#^text/#i, split(/\s*,\s*/, $env_accept)) ) ;
    &non_text_die unless $env_accept ne '' ;
}


# For a potential banner ad, intercept request if it looks like an image is
#   requested, i.e. unless the Accept: header allows either text/... or */... .
if ($images_are_banned_here) {
    &skip_image unless grep(m#^(text|\*)/#i, split(/\s*,\s*/, $env_accept) ) ;
}


# $base_url must be set correctly at any time &full_url() may be called.
#   &fix_base_vars() must be called as well, to set $base_scheme, $base_host,
#   $base_path, and $base_file.
# Unfortunately, the base URL may change over the course of this program.  We
#   will keep it set based on whatever info we have so far, i.e. request URI,
#   then e.g. HTTP response headers, then e.g. <base> tag (which happens to
#   be in the reverse order of the ultimate precedence).
$base_url= $URL ;
&fix_base_vars ;   # must be called whenever $base_url is set


# Redirect if $URL matches one of the patterns in %REDIRECTS.
if (defined $REDIRECTS{$host}) {
    my($s1, $s2)= @{$REDIRECTS{$host}}[0,1] ;
    &redirect_to(full_url($URL)) if $URL=~ s/$s1/$s2/ ;
}


# The next two variables $default_style_type and $default_script_type must be
#   kept up-to-date throughout the run of this program, just like $base_url
#   and its related variables.  They should always be canonicalized to
#   lowercase (MIME types are case-insensitive).
# Note that if these aren't handled carefully, then there could be a privacy
#   hole-- for example, style sheets of a script type could cause execution of
#   script content.

# Any style content ("style" attributes, <style> elements, or external
#   style sheets) that does not have a type defined uses the default style
#   sheet language. That should be specified in a Content-Style-Type: header
#   or equivalent <meta> tag, but if not then the default is text/css.
# This *should* only be needed for style attributes, but if the other two
#   forms of style content erroneously don't specify a type then it could be
#   used for them.
$default_style_type= 'text/css' ;

# Any script content (intrinsic events attributes (i.e. those named "on___")
#   or <script> elements) that does not have a type defined uses the default
#   script language.  That should be specified in a Content-Script-Type: header
#   or equivalent <meta> tag, but if not then the default is
#   application/x-javascript.
# This *should* only be needed for intrinsic event attributes, but if <script>
#   elements erroneously don't specify a type then it could be used for them.
# Unfortunately, MSIE doesn't always recognize "application/x-javascript",
#   even though that's the only strictly correct MIME type for JavaScript (it
#   does recognize the common "text/javascript").  However, $default_script_type
#   is only used to pass to proxify_block() or to compare to a script regex,
#   so we can keep it as the correct "application/x-javascript".
$default_script_type= 'application/x-javascript' ;


# Parse the cookie for real cookies and authentication information.  Also
#   sets session IDs, potentially.
($cookie_to_server, %auth)= &parse_cookie($ENV{'HTTP_COOKIE'}, $path, $host, $port, $scheme) ;

# Read cookies from database if using the database.
$cookie_to_server= &get_cookies_from_db($path, $host, $port, $scheme)  if $USE_DB_FOR_COOKIES ;


#--------------------------------------------------------------------------
#    Retrieve the resource into $body using the correct scheme,
#      also setting $status, $headers, and $is_html (all globals).
#      $is_html indicates whether the original resource is HTML, not
#      if a generated response is in HTML (e.g. an error message).
#      More accurately, it indicates whether we should proxify the resource
#      (note that HTML downloaded by a JS XMLHttpRequest object should not
#      be proxified, so in that case $is_html is false).
#    $response_sent might be set, indicating the response was sent by the
#      subroutine.  This is appropriate for streaming media, for example.
#--------------------------------------------------------------------------

if ($scheme eq 'http') {
    &http_get ;
} elsif ($scheme eq 'https') {
    &http_get ;
} elsif ($scheme eq 'ftp') {
    &ftp_get ;
}

#--------------------------------------------------------------------------
#    Modify entire response to point back through this script
#--------------------------------------------------------------------------

# If the resource is HTML (and not empty), update all URLs in all tags that
#   refer to URLs.  Plus a bunch of other stuff.

# jsm-- this structure has gotten sloppy.  Probably should integrate this
#   into http_get() etc.
if ( $is_html  && ($body ne '') && !$response_sent ) {

    $body= &proxify_html(\$body, 1) ;

    # Must change to byte string before compressing or sending.
    if (defined $charset) {
	eval { $body= encode($charset, $body) } ;
	&malformed_unicode_die($charset) if $@ ;

	# gzip the response body if we're allowed and able.
	if ($ENV{HTTP_ACCEPT_ENCODING}=~ /\bgzip\b/i) {
	    eval { require IO::Compress::Gzip } ;
	    if (!$@) {
		my $zout;
		IO::Compress::Gzip::gzip(\$body => \$zout)
		    or HTMLdie("Couldn't gzip: $IO::Compress::Gzip::GzipError") ;
		$body= $zout ;
		$headers= "Content-Encoding: gzip\015\012" . $headers ;
	    }
	}
    }

    # Change Content-Length header, since we changed the content
    $headers=~ s/^Content-Length:.*\012/
		 'Content-Length: ' . length($body) . "\015\012"/mie ;

}



#--------------------------------------------------------------------------
#    Send response back to user
#--------------------------------------------------------------------------

# If the response has not already been sent, print the status line, headers,
#   and the entire (possibly modified) resource.
# The $response_sent flag was added purely to support streaming media and
#   large files.
if (!$response_sent) {
    if ($ENV{'REQUEST_METHOD'} eq 'HEAD') {
	print $STDOUT $status, $headers ;
    } elsif ($is_html) {
	print $STDOUT $status, $headers, $body ;
	# print $debug ;   # handy for sprinkling checks throughout the code

    } else {
	print $STDOUT $status, $headers, $body ;
    }
}


# We could iron out all the goto's if we wanted....
ONE_RUN_EXIT:

close(S) ;
untie(*S) ;
eval { alarm(0) } ;   # use eval{} to avoid failing where alarm() is missing


# Put this back in to run speed trials
#if ($is_html) {
#    # OK, let's time this thing
#    my($eutime,$estime)= (times)[0,1] ;
#    open(LOG,">>proxy.log") ;
#    print LOG "full times: ", $eutime-$sutime, " ", $estime-$sstime,
#        " ", time-$starttime, "  URL: $URL\n" ;
#    close(LOG) ;
#}


}  # sub one_run {



# Main block


# Because of problems assigning STDIN and STDOUT to dup'ed tied filehandles, we
#   just use these variables for IO, and keep them up to date.
$STDIN= \*STDIN ;
$STDOUT= \*STDOUT ;


# If not running as a normal CGI or mod_perl script...
if (!$ENV{GATEWAY_INTERFACE}) {
    my $cmd= shift(@ARGV) ;
    my($num_processes, $max_requests, $port_arg, $wants_help) ;
    GetOptions('num-processes|n:i' => \$num_processes,
	       'max-requests|m:i' => \$max_requests,
	       'port|p:i' => \$port_arg,
	       'help|h|?' => \$wants_help)  or die "bad options-- try '$0 -?' for help\n" ;
    print(<<EOU), exit  if $wants_help or $cmd eq '' ;
Usage:
  $0  command  [ -n num_processes ]  [ -m max_requests ]  [ -p port ]

Parameters:
  command
    ... where command is one of:
      install-modules  install all optional Perl (CPAN) modules
      purge-db         purge the database of old data, which must be
			 done periodically if using a database
      start-fcgi       start FastCGI server processes (see -n and -m parameters)
      start-server     start the embedded server process (see -p parameter)
  -n, --num-processes  num_processes
    ... where num_processes is a positive integer: this sets how many
      FastCGI processes will be started and maintained (default=$FCGI_NUM_PROCESSES)
  -m, --max-requests  max_requests
    ... where max_requests is a positive integer:  this limits how
      many requests a single FastCGI process can handle before restarting
      (default=$FCGI_MAX_REQUESTS_PER_PROCESS)
  -p, --port  port
    ... where port is the port number you want the embedded server to
      listen on (default=443)
  -?, -h, --help
    print this usage message

Examples:
  $0 -c install-modules
  $0 -c purge-db
  $0 -c start-fcgi -n 1000

EOU


    # Start the FastCGI process manager.
    if ($cmd eq 'start-fcgi') {
	$num_processes||= $FCGI_NUM_PROCESSES ;
	$max_requests||= $FCGI_MAX_REQUESTS_PER_PROCESS ;
	install_modules(qw(Net::SSLeay  IO::Compress::Gzip  IO::Compress::Deflate)) ;
	require_with_install('FCGI', 1) ;
	require_with_install('FCGI::ProcManager', 1) ;
	$RUN_METHOD= 'fastcgi' ;
	my $proc_mgr= FCGI::ProcManager->new( { n_processes => $num_processes,
						max_requests => $max_requests } ) ;
	$proc_mgr->pm_manage() ;
	my $socket= FCGI::OpenSocket($FCGI_SOCKET, 10) ;
	chmod(0777, $FCGI_SOCKET) unless $FCGI_SOCKET=~ /^:/ ;   # jsm-- not terribly secure....
	my $request= FCGI::Request(\*STDIN, \*STDOUT, \*STDERR, \%ENV, $socket) ;
	while ($request->Accept>=0) {
	    $proc_mgr->pm_pre_dispatch() ;    # required for FCGI::ProcManager
	    init unless $HAS_INITED;
	    eval { one_run() } ;
	    warn $@ if $@ ;   # jsm-- should do anything else here?
	    $proc_mgr->pm_post_dispatch() ;   # required for FCGI::ProcManager
	}
	FCGI::CloseSocket($socket);


    # Use the embedded server (daemon).
    } elsif ($cmd eq 'start-server') {
	$port_arg||= 443 ;
	install_modules(qw(Net::SSLeay  IO::Compress::Gzip  IO::Compress::Deflate)) ;
	eval { require Net::SSLeay } ;  # don't check during compilation
	die "Running CGIProxy as a daemon requires the Net::SSLeay module.\n" if $@ ;
	$RUN_METHOD= 'embedded' ;

	# We need the port before calling init(), which complicates this.
	my($LOCK_FH, $port, $pid)= create_server_lock('http.run') ;
	if ($LOCK_FH) {
	    my $HTTPS_LISTEN ;
	    ($HTTPS_LISTEN, $port)= new_server_socket($port_arg) ;
	    $<= $>= $RUN_AS_USER  if $RUN_AS_USER and $>==0 ;
	    &set_ENV_UNCHANGING($port) ;
	    %ENV= %ENV_UNCHANGING ;       # needed for init
	    init ;
	    $pid= spawn_generic_server($HTTPS_LISTEN, $LOCK_FH, \&handle_http_request, 0, 1) ;
	}
	my $hostname= hostfqdn() ;
	$hostname=~ s/\.$// ;   # bug in hostfqdn() may leave trailing dot
	my $portst= $port==443  ? ''  : ":$port" ;
	print "URL of this proxy:  https://$hostname$portst/$SECRET_PATH/\n\nProcess ID:  $pid\n" ;


    # This needs to be done periodically, to clear out old cookies and sessions.
    #   Best to put it in a cron job.
    } elsif ($cmd eq 'purge-db') {
	init ;
	purge_db() ;


    } elsif ($cmd eq 'install-modules') {
	install_modules(qw(Net::SSLeay  IO::Compress::Gzip  IO::Compress::Deflate)) ;
    }



# ... else is running as normal CGI or mod_perl script.
} else {
    $RUN_METHOD= $ENV{MOD_PERL}  ? 'mod_perl'  : 'cgi' ;
    init unless $HAS_INITED;
    eval { one_run() } ;
    # We'd act on $@, but it does what we need below anyway.
}


EXIT:

# Catch-all-- if any handles are still open, close them here.  Some error
#   handling relies on this happening.  Also cancel existing alarm.
# These are basically for mod_perl, and unneeded if running as a CGI script.
close(S) ;
untie(*S) ;
eval { alarm(0) } ;   # use eval{} to avoid failing where alarm() is missing

exit if $RUN_METHOD eq 'cgi' ;    # mod_perl scripts must not exit


#--------------------------------------------------------------------------
#   DONE!!
#--------------------------------------------------------------------------


#--------------------------------------------------------------------------
# proxify_html()-- Modify entire response to point back through this script
#--------------------------------------------------------------------------
#
# NOTE: IT IS IMPORTANT TO DO THIS AS COMPLETELY AS POSSIBLE!  IF A
# USER UNKNOWINGLY GOES TO A PAGE DIRECTLY AND NOT THROUGH THIS PROXY,
# HE/SHE MAY REVEAL HIM/HERSELF IN AN UNINTENDED WAY.
#
#--------------------------------------------------------------------------
# These were notes to myself from testing the speed of different methods.
#   Names like "nph-proxy2" refer to different modifications.  This version,
#   the fastest, was called nph-proxy2b.
#
# If YOU figure out a faster method, please tell me about it!
#
# It would certainly be faster if rewritten in C, because you could very
#   quickly read each character from the input and write it to the output,
#   maintaining state and altering the data stream as needed.  How much
#   faster is unclear, since the regular expression governing the main
#   while() loop below (as of version 2.0) is fairly efficient, and is
#   in effect handled in C by the Perl interpreter.
#
#--------------------------------------------------------------------------
#
# [This version is nph-proxy2b:  Break into @body array, do not use
#   %urlsin to test if tags should be updated, replacement strings
#   use (a|b|c) syntax.]
#
# [%urlsin was an associative array that listed tags and attributes that
#   may contain URLs, declared like:
#  %urlsin= ('a', 'href',
#            'applet', 'codebase',
#            'fig', 'src|imagemap',
#            'form', 'action|script',  ...
#           ) ;
# ]
#
# This is by far the most time-consuming part of the script, the updating
#   of all URLs in an HTML file.
#
# Results of informal speed testing (not what I expected):
#   Breaking into @body array instead of one big string definitely saves
#       significant time-- compare nph-proxy2 to nph-proxy1.  One test
#       showed a time saving of 1/3 to 1/2.
#   Using a %urlsin array does NOT seem to save time, even when only used
#       as boolean test to see if tag might contain URL-- compare nph-proxy2
#       to nph-proxy3, nph-proxy4, and (most similar) nph-proxy5.  Oh well.
#   It seems that reading one tag at a time, converting, and sending it
#       through does NOT save elapsed time over reading all tags before
#       converting, like I thought it would.  Both the CPU and elapsed
#       time are longer for one-tag-at-a-time approach-- compare
#       nph-proxy2 and nph-piper2.
#
#   Results of nph-proxy2 (blocks for each tag) to nph-proxy2b
#   (single "(att1|att2|att3)" style regex) testing:
#       Mixed results, but overall, using a single regex (nph-proxy2b)
#       takes less CPU "user time", about the same "system time", and
#       slightly more elapsed time than nph-proxy2; I don't know why.
#       The elapsed time is slightly more both within the script and at
#       the HTTP client's end.  All differences are less than 10% on
#       average, and nph-proxy2b occasionally shows LESS elapsed time
#       than nph-proxy2.  CPU time is always less for nph-proxy2b than
#       for nph-proxy2.
#   Since the bottleneck of CPU time is tighter than for elapsed time,
#       and since the elapsed-time loss is less than the CPU time gain,
#       let's go with nph-proxy2b (not that it really makes much difference).
#       Besides, the code is easier to read that way.
#
# So basically, breaking into @body array helps, but not much else does.
#
#--------------------------------------------------------------------------
# 8-4-98 JSM: Found a bug in the regex, so changed it.  It more resembles
#   nph-proxy2.cgi now.
#--------------------------------------------------------------------------


# This routine proxifies an entire block of HTML, which may in turn contain
#   scripts, stylesheets, comments, etc. that need to be proxified in their
#   own ways.
# The first parameter is either a scalar to be proxified, a reference to a
#   scalar (fastest for long strings), or a reference to a list of scalars
#   that need to be joined before proxifying.  The second parameter is a
#   flag that indicates whether this is a full page being proxified, or just
#   an HTML fragment (mostly to know whether we can insert something or not).
# The return value is one long scalar, the proxified HTML.
# This routine normally exits immediately if it finds a <frameset> tag.  This is
#   usually appropriate, but it can be avoided by setting the third parameter,
#   such as when calling this from inside a (normal, non-conditional) comment.
#   This flag should be preserved in nested calls when needed.  Rarely relevant.
# Note that since this routine calls full_url(), $url_start and the $base_ vars
#   must be set before calling this.
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_proxify_html() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a (highly abbreviated) Perl-to-JavaScript translation of this routine.
#   Also note that parts of this routine are represented by other JavaScript
#   subroutines, namely _proxy_jslib_proxify_comment(),
#   _proxy_jslib_proxify_script_block(), _proxy_jslib_proxify_style_block()
#   _proxy_jslib_proxify_decl_bang(), _proxy_jslib_proxify_decl_question(), and
#   _proxy_jslib_proxify_element() .

sub proxify_html {
    my($body_ref, $is_full_page, $no_exit_on_frameset)= @_ ;
    my(@out, $start, $comment, $script_block, $style_block, $decl_bang, $decl_question, $tag,
       $body_pos, $html_pos, $head_pos, $first_script_pos, $out_start,
       $has_content, $in_noscript, $in_title, $title, $full_insertion, $body2,
       $current_object_classid) ;
    my($ua_is_MSIE)= $ENV{'HTTP_USER_AGENT'}=~ /MSIE/ ;   # used in tight loops

    # Allow first parameter to be reference to list of values to be joined.
    $body_ref= \(join('', @$body_ref)) if ref($body_ref) eq 'ARRAY' ;

    # Allow first parameter to be string instead of reference, for convenience.
    if (!ref($body_ref)) {
	$body2= $body_ref ;
	$body_ref= \$body2 ;
    }

    # Read in the insertion if it will be needed.  Read it now instead of
    #   later, so certain JavaScript that depends on tag counts inside the
    #   insertion can be handled correctly.
    $full_insertion= &full_insertion($URL,0)   if $is_full_page ;


    # Iterate through $body, matching "chunks" as appropriate.  In HTML, the
    #   only sections that are interpreted as other than HTML are comments,
    #   within <script> blocks, within <style> blocks, and SGML declarations.
    #   Thus, match comments, <script> blocks, <style> blocks, and SGML
    #   declarations before matching any simple HTML tag.
    # Note that in a regex, alternatives are matched in order, which we take
    #   advantage of here-- the general case of a tag is matched after all
    #   others.
    # HTML outside of tags isn't supposed to have "<", but browsers support it
    #   as a literal string if it's not followed by [a-zA-Z/].  So we support that
    #   in the first line of the regex, or else it's a privacy hole.
    # Comment formats have an unfortunate history.  Technically they're
    #   supposed to end on "--\s*>" (actually it's a bit more complicated than
    #   that), but many HTML authors merely end them on ">".  Browsers seem to
    #   first try to end a comment on "--\s*>", but if that's not available
    #   they end a comment on the first ">".  In addition, some browsers don't
    #   allow whitespace between "--" and ">".  Put that together and it's not
    #   easy to know where a browser will end comment processing and restart
    #   HTML processing.  In general, it's usually safer here to treat comment
    #   as HTML than HTML as comment, so here we end comments as early as the
    #   browser might end them: if a future "-->" exists, then that means end
    #   on "--\s*>", but if a future "-->" doesn't exist, then it means end on
    #   ">".  Thus the zero-width lookahead assertions in the regex below.  Not
    #   perfect.  :P  Would be better to tailor actions to browser types.  We
    #   could err towards longer comments for safety rather than shorter, if we
    #   removed comments entirely.
    # For info about non-HTML blocks in an HTML document, see
    #   http://www.w3.org/TR/html40/appendix/notes.html#h-B.3.2
    # Script and style blocks are supposed to end with the first "</" string,
    #   but in fact browsers seem to end those blocks at the actual </script>
    #   or </style> tags.  This is most likely what the HTML author expects
    #   anyway, though it violates the HTML spec.  In this script, we should
    #   over-proxify rather than under-proxify, so we'll end those blocks on
    #   those end tags as browsers (erroneously) do.
    # Worse, Konqueror allows the string "</script>" inside JS literal strings,
    #   i.e. doesn't end the script block on them.  Netscape does end the block
    #   there, and both browsers end style blocks on embedded </style> strings.
    # Because it's a given that we can't anonymize scripts completely, but
    #   we do want to anonymize HTML completely, we'd rather accidentally
    #   treat script content as HTML than the other way around.  So err on
    #   ending the <script> block too soon for some browsers, i.e. end on
    #   the first "</script>" regardless of whether it's in a string.
    #   (We'd end on "</", but *no* browser seems to do that.)
    # Script content can can exist in:  <script> blocks, conditional comments,
    #   intrinsic event attributes ("on___" attributes), script macros, and
    #   the MSIE-specific "dynamic properties".  These can be removed or
    #   proxified, depending on the settings of $scripts_are_banned_here and
    #   $PROXIFY_SCRIPTS.
    # Script content can also exist elsewhere when its MIME type is explicitly
    #   given (for example, in a <style> block); these cases will be handled
    #   (i.e. removed, proxified, or neither) when proxify_block() is called
    #   with those MIME types.


    # second line was: (?:(<!--.*?--\s*> | <!--.*?> )  # order is important
    while ( $$body_ref=~ m{\G( (?> [^<]* ) (?> < (?![a-zA-Z/!\?]) [^<]* )* )
			     (?:(<!--(?=.*?-->).*?--\s*> | <!--(?!.*?-->).*?> )
			       |(<script\b.*?</script\b.*?>)
			       |(<style\b.*?</style\b.*?>)
			       |(<![^>]*>?)
			       |(<\?[^>]*>?)
			       |(<[^>]*>?)
			     )?
			  }sgix )
    {

	# Above regex must be in scalar context to work, so set vars here.
	($start, $comment, $script_block, $style_block, $decl_bang, $decl_question, $tag)=
	    ($1, $2, $3, $4, $5, $6, $7) ;

	# Handle page titles here.  This includes extracting one into $title,
	#   and clearing it if $REMOVE_TITLES is set.  Slightly hacky.
	# We assume the page title is the $start before a </title> end tag.
	#   HTML authors may erroneously put tags in there and mess up our
	#   assumption, but it will only affect display, not privacy.
	# To avoid checking this regex for every tag, stop after a <body> tag
	#   has been found.  This means any erroneous <title> blocks after
	#   that won't be removed.  If this ever matters, we can change it.
	if ($tag && !$body_pos && $tag=~ m#^</title\b#i) {
	    $start= ''  if $REMOVE_TITLES ;
	    $title= $start ;
	}


	# Pass the text between tags through to the output.
	push(@out, $start) ;

	# Used when there is illegal early script content (see continue block).
	$out_start= @out ;

	# Don't insert anything into a document that has no text content.
	#   Otherwise, <frameset> tags (either hard-coded or written by JS)
	#   will not take effect--- any text content on the page disables
	#   framesets, in tested browsers.  A document with both text content
	#   and <frameset> tags is illegal anyway.
	$has_content||= $start=~ /\S/ unless $in_noscript || $in_title ;


	# Handle $tag match first, because it's the most common (though it's
	#   the last in the regex above).  Other cases to handle comments etc.
	#   follow this huge block, in "elsif {}" blocks.
	# NOTE: IF YOU MODIFY THIS BLOCK, then be sure to review and possibly
	#   modify the corresponding routine _proxy_jslib_proxify_element() in the
	#   JavaScript library, far below in the routine return_jslib().  It is
	#   a (highly abbreviated) Perl-to-JavaScript translation of this block.
	if ($tag) {

	    my($tag_name, $attrs, %attr, $name, $rebuild) ;

	    # Tag and attribute names match ([A-Za-z][\w.:-]*), I believe implied
	    #   by http://www.w3.org/TR/REC-html40/types.html#type-name .
	    ($tag_name, $attrs)= $tag=~ /^<\s*(\/?\s*[A-Za-z][\w.:-]*)\s*([^>]*)/ ;
	    $tag_name=~ s#^/\s*#/# ;
	    $tag_name= lc($tag_name) ;

	    # If scripts are removed, then we might as well display the blocks
	    #   within <noscript>.  Change <noscript> and </noscript> to <div>
	    #   and </div>, since <noscript> acts very close to <div> when it
	    #   is activated.  This preserves element attributes like lang, dir,
	    #   style, etc.
	    # Also use this block to handle $in_noscript and $in_title, which
	    #   are used to set $has_content correctly.
	    if ($tag_name eq 'noscript') {
		$in_noscript++ ;
		if ($scripts_are_banned_here) {
		    $tag=~ s/^<\s*noscript\b/<div/i ;
		    $tag_name= 'div' ;
		    $rebuild= 1 ;
		}
	    } elsif ($tag_name eq '/noscript') {
		$in_noscript-- if $in_noscript>0 ;
		push(@out, '</div>'), next if $scripts_are_banned_here ;
	    } elsif ($tag_name eq 'title') {
		$in_title++ ;
	    } elsif ($tag_name eq '/title') {
		$in_title-- ;
	    }

	    # Remember positions of first <html>, <head>, and <body> tags for
	    #   insertions later.
	    # Must do before big switch below, since a tag with no attributes
	    #   won't get that far.
	    $html_pos= @out+1  if !$html_pos && ($tag_name eq 'html') ;
	    $head_pos= @out+1  if !$head_pos && ($tag_name eq 'head') ;
	    $body_pos= @out+1  if !$body_pos && ($tag_name eq 'body') ;

	    # Clear $current_object_classid as needed.
	    $current_object_classid= ''  if $tag_name eq '/object' ;

	    # If it's a frame document, then call return_frame_doc().
	    # Only bother with this if we're doing an insertion.
	    # MUST be careful not to do this when $is_in_frame!  Else will recurse!
	    # This is the only exit point in proxify_html() other than the end.
	    &return_frame_doc(&wrap_proxy_encode($URL), $title)
		if ($tag_name eq 'frameset') && $doing_insert_here  && !$is_in_frame
		   && !$no_exit_on_frameset ;

	    # Close <div> block that surrounds entire original page.
	    push(@out, "</div>\n") if $tag_name eq '/body' ;

	    # Pass tag through if it has no attributes, or if it doesn't parse
	    #   above (which would make $attrs undefined).  This includes end tags.
	    push(@out, $tag), next   if ($attrs eq '') ;


	    # Parse attributes into %attr.
	    # Regex below must be in scalar context for /g to work.
	    # In the case of duplicate attributes, browsers tend to use the first.
	    # A hack is here to handle erroneous HTML attributes that contain
	    #   ">" :  if an unclosed string is found in $attrs, then read up
	    #   to the next ">", add that to the tag, and restart the parsing.

	    PARSE_ATTRS: {
#		while ($attrs=~ /([A-Za-z][\w.:-]*)\s*(?:=\s*(?:"([^">]*)"?|'([^'>]*)'?|([^'"][^\s>]*)))?/g ) {
		while ($attrs=~ /([A-Za-z][\w.:-]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^'"][^\s>]*)|(['"])))?/g ) {
		    if (defined($5)) {
			# Again, next line only works in scalar context.
			$$body_ref=~ /\G([^>]*)(>?)/gc ;
			my($extra, $close)= ($1, $2) ;
			# exit loop if at end of string
			last if ($extra eq '') and ($close eq '') ;
			$attrs.= '>' . $extra ;
			$tag.=   $extra . $close ;
			%attr= () ;
			redo PARSE_ATTRS ;
		    }

		    $name= lc($1) ;
		    $rebuild= 1, next if exists($attr{$name}) ; # duplicate attr
		    $attr{$name}= &HTMLunescape(defined($2) ? $2
					      : defined($3) ? $3
					      : defined($4) ? $4
					      : '' ) ;
		}
	    }


	    # Intrinsic event attributes, aka "(Java-)script attributes", are
	    #   assumed to be all attributes whose names start with "on".  This
	    #   is the case with HTML 4.01 as of late 1999.
	    # Script macros, aka the Netscape-specific "JavaScript entities",
	    #   have the form "&{ script-content };" and may appear within	
	    #   (and thus invoke JavaScript within) *any* HTML attribute.
	    #   Other browsers may emulate Netscape, so we handle these for
	    #   all browsers. 
	    # MSIE-specific "dynamic properties" can be in style attributes.
	    #   I can't find a definitive reference for their syntax (tell me
	    #   if you know of one), so in handling them we err on the safe
	    #   side and e.g. remove all style attributes that contain the
	    #   string "expression(".  I think I've seen "function()" used
	    #   too, so handle those.  But I'm not very familiar with these.
	    # As far as I can tell, the language used for "dynamic properties"
	    #   is text/jscript (Microsoft's JavaScript variant).
	    # There's an obscure problem with Netscape, script macros, and
	    #   character entities:  Netscape doesn't allow a block inside &{};
	    #   to contain character entities, though quoted strings inside
	    #   that block *can* (and sometimes *must*).  This seems to be in
	    #   violation of the HTML and SGML specs, as far as I can tell; see:
	    #     http://www.w3.org/TR/html40/types.html#h-6.14
	    #     http://www.w3.org/TR/html40/appendix/notes.html#h-B.7
	    #     http://www.w3.org/TR/html40/appendix/notes.html#h-B.3.2
	    #   Anyway, this messes with our HTMLunescape()'ing and
	    #   HTMLescape()'ing.  It will only matter when $PROXIFY_SCRIPT
	    #   is on (meaning bulletproof anonymity can't be too critical),
	    #   and rarely at that, so we'll let it slide for now.  We can
	    #   revisit this later if it becomes an issue.
	    # Netscape also allows quotes inside script macros that match the
	    #   outer enclosing quotes, but for now this script doesn't allow
	    #   those.  (I'm not sure Netscape should either.)
	    # Intrinsic event attributes may have character entities in them
	    #   (even though any contained script macros cannot, in Netscape's
	    #   implementation).


	    # If so configured, remove or proxify any script elements in each tag.
	    if ($scripts_are_banned_here) {

		# Remove intrinsic event attributes, which start with "on".
		# Also remove script macros, by removing all attributes with
		#   "&{" in them (which unfortunately removes any attributes
		#   that innocently contain that string too).  Remove the
		#   entire attribute.
		my(@remove_attrs)= grep(/^on/ || $attr{$_}=~ /&{/ , keys %attr) ;
		delete @attr{ @remove_attrs }, $rebuild=1   if @remove_attrs ;

	    } elsif ($PROXIFY_SCRIPTS) {

		# Proxify any script macros first.
		foreach (keys %attr) {
		    $attr{$_}=~ s/&{(.*?)};/
				 '&{' . (&proxify_block($1, $default_script_type))[0] . '};'
				 /sge
			&& ($rebuild= 1) ;
		}

		# Then, proxify all intrinsic event attributes.
		# This is imperfect but probably OK-- see notes above regarding
		#   Netscape, script macros, character entities, and our use
		#   of HTMLescape() and HTMLunescape().
		foreach (grep(/^on/, keys %attr)) {
		    $attr{$_}= (&proxify_block($attr{$_}, $default_script_type))[0] ;
		    $rebuild= 1 ;
		}
	    }


	    # Proxify style attribute, which could exist in almost any tag.
	    # Handle any MSIE-specific "dynamic properties" here instead of
	    #   above, to avoid extra work on every tag.
	    if (defined($attr{style})) {

		# Remove or proxify any "dynamic properties" in style
		#   attributes.  Only bother if user is using MSIE.
		if ($ua_is_MSIE) {
		    if ($scripts_are_banned_here) {
			delete($attr{style}), $rebuild=1
			    if $attr{style}=~ /(?:expression|function)\s*\(/i ;

		    } elsif ($PROXIFY_SCRIPTS) {
			# Proxify any strings inside "expression()" or "function()".
			$attr{style}= &proxify_expressions_in_css($attr{style}), $rebuild= 1
			    if $attr{style}=~ /(?:expression|function)\s*\(/i ;
		    }
		}

		$attr{style}= (&proxify_block($attr{style}, $default_style_type))[0], $rebuild=1 ;
	    }



	    # Now, proxify the tag and its attributes based on which tag it is.
	    # This is a complete list of HTML tags/attributes that may include
	    #   a URL, to the best of my knowledge.  This list includes all
	    #   URL-type attributes defined in HTML 4.0 (as of 7-31-98), an
	    #   earlier HTML DTD as of 9-17-96, and any tags documented on
	    #   Michael Hannah's comprehensive HTML reference (as of 9-17-96;
	    #   Sandia has since forced him to remove the page).  The latter
	    #   included non-standard tags found to be used by Netscape or
	    #   Microsoft.
	    # If anyone knows of a well-maintained list of standard and
	    #   non-standard tags/attributes with URLs in them, please let me
	    #   know!!
	    # Tags are roughly in order from most-common to least common, for
	    #   speed.  Beyond that, they're roughly alphabetical.  Also,
	    #   they're roughly grouped as appropriate.  In the future, they
	    #   may be called instead via a hash of function references
	    #   (e.g. "&$do_tag{$tag_name}"), if we determine that the hash
	    #   lookup plus function call is faster than the current string
	    #   comparisons.
	    # We'll only get here for tags containing attributes.
	    # Note that most of these are very rarely used, if ever.  They're
	    #   included for safety, since we don't want an anonymous user
	    #   accidentally revealing themselves because of a non-anonymized
	    #   URL.
	    # Earlier versions of this script used a long regex to extract
	    #   and modify attributes.  Now, tags are fully parsed into
	    #   attributes, which takes a little longer but operates much more
	    #   cleanly and reliably.  The code is easier to work with too.
	    # Denoting which of these are for images/binaries might be helpful,
	    #   if we need more elaborate text-only support.

	    # Notes regarding frame support:
	    # One of the flags in PATH_INFO indicates whether the page will be
	    #   displayed in a frame, so we know whether or not we can insert a
	    #   header.  Most links keep the frame flag of their containing
	    #   page, but some links can change it-- it's set in <frame> tags,
	    #   and it's cleared in various links that exit a framed page.  For
	    #   both cases, we use the full_url_by_frame() routine instead of
	    #   full_url().  (You can think in terms of entering or leaving
	    #   "frame mode".)
	    # The links that set the frame flag are <frame> and <iframe>.  The
	    #   links that can clear it are <a>, <area>, <link>, and <form>,
	    #   when their target attribute is either "_top" or "_blank".  In
	    #   addition, the <base> tag can have a target attribute, which is
	    #   the default target for any of these tags lacking their own.  So
	    #   we maintain a variable $base_unframes that tells us whether the
	    #   current <base> target would make a link exit frames (i.e. it's
	    #   either "_top" or "_blank", or at least that's our best guess).
	    #   We check $base_unframes when handling <a>, <area>, <link>, and
	    #   <form> tags to set the frame flag correctly.
	    # Not all frame exits will be caught.  :(  This is because for any
	    #   given target attribute, we don't know whether it leads to a new
	    #   open window, or another frame in the existing window.  It could
	    #   hypothetically be fixed *somewhat* by maintaining some list of
	    #   which target names identify frames, based on the immediate
	    #   browsing history (i.e. record the frame name when a <frame> tag
	    #   is processed).  This would be rather elaborate, I think.
	    # This only matters in that if a link causes the user to leave
	    #   frames in a way we don't catch, then any HTML insertion may not
	    #   display properly.  This does NOT affect anonymity (whether the
	    #   user is still surfing through the proxy); it ONLY affects the
	    #   display of the inserted HTML.
	    # Apparently, Netscape only checks a matching prefix for _top and
	    #   _blank, i.e. "_topxx" and "_blankxx" act like _top and _blank.
	    #   MSIE works correctly.



		 #####   BEGIN TAG-SPECIFIC PROCESSING   #####



	    # Handle <a> tag, which only entails updating the href attribute,
	    #   but that includes deframing as needed (and *would* include
	    #   embedding the type code in the URL, but see next paragraph).
	    # Browsers are inconsistent in whether a tag's "type" attribute
	    #   takes precedence over actual Content-Type: header, or vice
	    #   versa.  It appears that for <link> tags, the type attribute
	    #   (erroneously) always takes precedence, while for the <a> tag
	    #   the type attribute is apparently ignored.  So to be consistent
	    #   with browsers, we need to IGNORE the expected type code for
	    #   the <a> tag.  In fact, we actually remove the type attribute
	    #   altogether to remove a privacy hole in any browsers that *do*
	    #   use it.  *sigh*  This wouldn't be a problem if <link>'s type
	    #   attribute was handled correctly by browsers, i.e. of lower
	    #   precedence than Content-Type:, but it's not. So the last part
	    #   of http_get() gets hacked a little, which leads to this hack.
	    #   (Another solution would be to add yet another flag into the
	    #   URL, a "linked-from-which-tag" flag.)
	    # Unlike other tags with type attribute, don't remove <a> tag
	    #   if it links to banned content.  It will only be activated
	    #   by user action, not automatically like the others.

	    if ($tag_name eq 'a') {
		# Remove type attribute altogether.
		delete $attr{type}, $rebuild=1   if defined($attr{type});

		if (defined($attr{href})) {

		    # If needed, detect if frame state might change.
		    # Deframe if (target unframes) or (no target and base target unframes)
		    if (   ($base_unframes && !defined($attr{target}))
			 || $attr{target}=~ /^_(top|blank)$/i         )
		    {
			$attr{href}= &full_url_by_frame($attr{href},0), $rebuild=1 ;
		    } else {
			$attr{href}= &full_url($attr{href}), $rebuild=1 ;
		    }


		    # If browsers were to handle all type attributes correctly
		    #   (see notes above), we'd use the block below to insert
		    #   the expected type into the linked-to URL.  Instead we
		    #   use the block above, because it's faster.

		    ## Could require $doing_insert_here here too to save a little
		    ##   time... may not keep frame state right, but wouldn't matter.
		    #my($link_unframe) ;
		    #$link_unframe=  ($base_unframes && !defined($attr{target}))
		    #              || $attr{target}=~ /^_(top|blank)$/i
		    #    if $is_in_frame ;

		    ## Use temporary copy of $url_start to call full_url() normally.
		    ## Only generate new value if is_in_frame flag has changed,
		    ##   or if type flag needs to be changed.
		    ## Verify that $attr{type} is a valid MIME type.
		    #local($url_start)= $url_start ;
		    #if ( ($attr{type} ne '') || $link_unframe ) {
		    #    ($attr{type})= $attr{type}=~ m#^\s*([\w.+\$-]*/[\w.+\$-]*)#, $rebuild=1
		    #        if  defined($attr{type}) && $attr{type}!~ m#^[\w.+\$-]+/[\w.+\$-]+$# ;
		    #    $url_start= $script_url . '/' .
		    #        &pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
		    #                    $e_hide_referer, $e_insert_entry_form,
		    #                    $link_unframe  ? 0  : $is_in_frame,
		    #                    lc($attr{type}))
		    #        . '/' ;
		    #}

		    #$attr{href}= &full_url($attr{href}), $rebuild=1 ;
		}



	    # Some browsers accept the faulty "<image>" tag instead of "<img>",
	    #   so handle that or else it's a privacy hole.  Changing <image>
	    #   tags to <img> works, plus lets such pages work in all browsers.
	    } elsif ($tag_name eq 'img' or $tag_name eq 'image') {
		$tag_name= 'img',                        $rebuild=1  if $tag_name eq 'image' ;

		# jsm-- better would be, if $RETURN_EMPTY_GIF is set, to
		#   modify src and lowsrc to be e.g. /x-proxy/images/emptygif
		#   so that it could be cached.
		if ($TEXT_ONLY && !$RETURN_EMPTY_GIF) {
		    delete($attr{src}) ;
		    delete($attr{lowsrc}) ;
		    $rebuild= 1 ;
		} else {
		    $attr{src}=    &full_url($attr{src}),    $rebuild=1  if defined($attr{src}) ;
		    $attr{lowsrc}= &full_url($attr{lowsrc}), $rebuild=1  if defined($attr{lowsrc}) ;
		}

		$attr{longdesc}= &full_url($attr{longdesc}), $rebuild=1  if defined($attr{longdesc}) ;
		$attr{usemap}= &full_url($attr{usemap}),     $rebuild=1  if defined($attr{usemap}) ;
		$attr{dynsrc}= &full_url($attr{dynsrc}),     $rebuild=1  if defined($attr{dynsrc}) ;


	    } elsif ($tag_name eq 'body') {
		$attr{background}= &full_url($attr{background}), $rebuild=1 if defined($attr{background}) ;



	    # <base> has special significance.
	    # The base URL and target in the <base> tag are handled differently
	    #   by different browsers.  Netscape keeps running track of the two
	    #   values: when it finds a <base> tag, it remembers any base URL
	    #   or target, and uses it for subsequent links.  In other words,
	    #   at any point in the document, the base URL and base target that
	    #   are in effect are the ones from the most recent (previous)
	    #   <base href> and <base target> attributes.  Konqueror, however,
	    #   only honors the *final* <base> tag in the document, and uses it
	    #   for all links.  Here we go with Netscape's approach.  If we
	    #   were to do it like Konqueror, we'd scan the document for <base>
	    #   tags before converting any HTML (earlier versions of the script
	    #   did this).
	    # Even if we occasionally e.g. use the wrong base URL in certain
	    #   browsers, it's probably privacy-safe-- URLs will still always
	    #   be absolute and point through the proxy.  We might just access
	    #   the wrong URL.  It's only an obscure possibility, and would
	    #   only happen in faulty HTML anyway (multiple <base> tags aren't
	    #   allowed).
	    # In this script, the base URL and base target are stored in the
	    #   $base_ vars, and in the $base_unframes flag.

	    } elsif ($tag_name eq 'base') {
		# Remember what we need to from this <base> tag.  Only set
		#   $base_url etc. if $attr{href} looks like an absolute URL
		#   (which it always should, but some pages have errors).
		$base_url= $attr{href}, &fix_base_vars
		    if defined($attr{href}) && $attr{href}=~ m#^[\w+.-]+://# ;
		$base_unframes= $attr{target}=~ /^_(top|blank)$/i ;

		# Then convert any href attribute normally.
		$attr{href}= &full_url($attr{href}), $rebuild=1  if defined($attr{href}) ;



	    } elsif ($tag_name eq 'frame') {
		$attr{src}=      &full_url_by_frame($attr{src},1), $rebuild=1 if defined($attr{src}) ;
		$attr{longdesc}= &full_url($attr{longdesc}),       $rebuild=1 if defined($attr{longdesc}) ;

	    } elsif ($tag_name eq 'iframe') {
		$attr{src}=      &full_url_by_frame($attr{src},1), $rebuild=1 if defined($attr{src}) ;
		$attr{longdesc}= &full_url($attr{longdesc}),       $rebuild=1 if defined($attr{longdesc}) ;


	    # <head>'s profile attribute can be a space-separated list of URIs.
	    } elsif ($tag_name eq 'head') {
		$attr{profile}= join(' ', map {&full_url($_)} split(" ", $attr{profile})),
		    $rebuild=1  if defined($attr{profile}) ;

	    } elsif ($tag_name eq 'layer') {
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;



	    } elsif ($tag_name eq 'input') {
		$attr{src}=        &full_url($attr{src}),        $rebuild=1  if defined($attr{src}) ;
		$attr{usemap}=     &full_url($attr{usemap}),     $rebuild=1  if defined($attr{usemap}) ;
		$attr{formaction}= &full_url($attr{formaction}), $rebuild=1  if defined($attr{formaction}) ;


	    # <form> tag needs special attention, here and elsewhere.
	    # is <form script='...'> attribute ever used, or even recognized
	    #    by any browser?  It's not defined in any W3C DTD.
	    } elsif ($tag_name eq 'form') {
		# Deframe if (target unframes) or (no target and base target unframes)
		if (   ($base_unframes && !defined($attr{target}))
		     || $attr{target}=~ /^_(top|blank)$/i         )
		{
		    $attr{action}= &full_url_by_frame($attr{action},0), $rebuild=1 if defined($attr{action}) ;
		} else {
		    $attr{action}= &full_url($attr{action}),            $rebuild=1 if defined($attr{action}) ;
		}

		if ($scripts_are_banned_here) {
		    delete($attr{script}), $rebuild=1 if defined($attr{script}) ;
		} else {
		    $attr{script}= &full_url($attr{script}), $rebuild=1  if defined($attr{script}) ;
		}



	    # The only special handling for <area> is to handle any deframing.
	    } elsif ($tag_name eq 'area') {
		# Deframe if (target unframes) or (no target and base target unframes)
		if (   ($base_unframes && !defined($attr{target}))
		     || $attr{target}=~ /^_(top|blank)$/i         )
		{
		    $attr{href}= &full_url_by_frame($attr{href},0), $rebuild=1  if defined($attr{href}) ;
		} else {
		    $attr{href}= &full_url($attr{href}), $rebuild=1  if defined($attr{href}) ;
		}




	    # Handle <link> tag.  If type attribute exists, include correct
	    #   expected-type flag in updated links for other attributes, e.g.
	    #   to handle external style sheets correctly when downloaded
	    #   later.  Also handle deframing as needed.  Remove <link> tag
	    #   altogether if type is a script type and scripts are banned.
	    #   Note that the type attribute indicates an *advisory* *expected*
	    #   MIME type, not a required type, though some browsers seem to
	    #   treat it erroneously as the ultimate authority.
	    # In Netscape, the Content-Style-Type: header has no effect in the
	    #   interpretation of external style sheets.  This is probably correct.
	    #   Thus, $default_style_type is not used here.
	    # See http://www.w3.org/TR/html40/struct/links.html#edef-LINK  and
	    #     http://www.w3.org/TR/html40/types.html#type-links

	    } elsif ($tag_name eq 'link') {
		# Verify that $attr{type} is a valid MIME type.
		($attr{type})= $attr{type}=~ m#^\s*([\w.+\$-]*/[\w.+\$-]*)#, $rebuild=1
		    if  defined($attr{type}) && $attr{type}!~ m#^[\w.+\$-]+/[\w.+\$-]+$# ;

		my($type)= lc($attr{type}) ;

		# When a type attribute is not given, some browsers erroneously
		#   use a default type of "text/css" for any <link> tag indicating
		#   a stylesheet, even to the point of overriding a subsequent
		#   Content-Type: header.  So set that default type here if it's
		#   a stylesheet, as indicated by the rel attribute.
		$type= 'text/css' if ($type eq '') && $attr{rel}=~ /\bstylesheet\b/i ;

		# Remove tag if it links to a script type and scripts are banned.
		next if $scripts_are_banned_here && $type=~ /^$SCRIPT_TYPE_REGEX$/io ;

		# Deframe if (target unframes) or (no target and base target unframes)
		my($link_unframe) ;
		$link_unframe=  ($base_unframes && !defined($attr{target}))
			      || $attr{target}=~ /^_(top|blank)$/i
		    if $is_in_frame ;

		# Use temporary copy of $url_start to call full_url() normally.
		# Only generate new value if type flag has changed or we're deframing.
		local($url_start)= $url_start ;
		if ($type ne '') {
		    $url_start= $script_url . '/' .
			&pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
				    $e_hide_referer, $e_insert_entry_form,
				    $link_unframe  ? 0  : $is_in_frame,
				    $type)
			. '/' ;
		} elsif ($link_unframe) {
		    $url_start= $url_start_noframe ;
		}

		$attr{href}= &full_url($attr{href}), $rebuild=1  if defined($attr{href}) ;
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;   # Netscape?
		$attr{urn}=  &full_url($attr{urn}),  $rebuild=1  if defined($attr{urn}) ;




	    # Handle <meta http-equiv> tags like real HTTP headers (though the
	    #   Netscape-only "url" attribute can be handled normally).
	    # Remove http-equiv attribute if content is empty, else may generate
	    #   empty cookie.
	    # Note that nonstandard headers like Link: and URI: may contain
	    #   "<>", which should be correctly escaped and unescaped elsewhere.

	    } elsif ($tag_name eq 'meta') {
		$attr{url}= &full_url($attr{url}), $rebuild=1  if defined($attr{url}) ;   # Netscape

		if (defined($attr{'http-equiv'}) && defined($attr{content})) {
		    $attr{content}= &new_header_value(@attr{'http-equiv', 'content'}) ;
		    delete($attr{'http-equiv'}) unless defined($attr{content}) ;
		    $rebuild= 1 ;
		}





	    # The <param> tag is special-- if its valuetype attribute is "ref",
	    #   then the value attribute is a URI.  Also, in this case it has a
	    #   type attribute which indicates an expected MIME type.
	    # In http://www.w3.org/TR/html40/struct/objects.html#edef-PARAM ,
	    #   we're told not to resolve the value URI; however, not doing so
	    #   could open a privacy hole, normally only when it's an absolute
	    #   URI.  So based on our priorities, we update the value URI here
	    #   iff it's an absolute URI.
	    # Note that <param> tags within certain <object> elements may also
	    #   need to be proxified; see the comments below, above the
	    #   <object> tag handling, for details about the classid, in
	    #   particular within MSIE's Active X control for Shockwave Flash.
	    # Firefox supports <param name="movie" value="..."> with no classid
	    #   in the <object>, so now we proxify such a tag regardless.

	    } elsif ($tag_name eq 'param') {

		# classid

		# Below is not needed anymore.
		# Handle any classid's specially.
		#if ($current_object_classid=~
		#    /^\s*clsid:\{?D27CDB6E-AE6D-11CF-96B8-444553540000\}?\s*$/i)
		#{
		    if (lc($attr{name}) eq 'movie') {
			# Retain query string for Flash apps.
			$attr{value}= &full_url($attr{value}, 1) ;
			$rebuild= 1 ;

		    # Hack here-- until we figure out how to parse .swz files
		    #   (Adobe's signed SWF libraries), we proxify certain
		    #   fields in the flashvars parameter.  Unreliable.  Ideally,
		    #   we'd proxify the .swz files when downloaded.
		    } elsif (lc($attr{name}) eq 'flashvars') {
			$attr{value}= proxify_flashvars($attr{value}) ;
			$rebuild= 1 ;
		    }



		#} elsif (lc($attr{valuetype}) eq 'ref') {
		if (lc($attr{valuetype}) eq 'ref') {
		    # Verify that $attr{type} is a valid MIME type.
		    ($attr{type})= $attr{type}=~ m#^\s*([\w.+\$-]*/[\w.+\$-]*)#, $rebuild=1
			if  defined($attr{type}) && $attr{type}!~ m#^[\w.+\$-]+/[\w.+\$-]+$# ;

		    my($type)= lc($attr{type}) ;

		    # Remove tag if it links to a script type and scripts are banned.
		    next if $scripts_are_banned_here && $type=~ /^$SCRIPT_TYPE_REGEX$/io ;

		    # Convert value attribute if needed.
		    if (defined($attr{value}) && ($attr{value}=~ /^[\w.+-]+:/)) {

			# Use a local copy of $url_start to call full_url() normally.
			# Only generate new $url_start if the type flag has changed.
			local($url_start)= $url_start ;
			if ($type ne '') {
			    $url_start= $script_url . '/' .
				&pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
					    $e_hide_referer, $e_insert_entry_form,
					    $is_in_frame, $type)
				. '/' ;
			}
			$attr{value}= &full_url($attr{value}) ;
			$rebuild= 1 ;
		    }
		}





	    # <applet> tags are handled much like <object> tags; see the
	    #   comments in that block to explain this block.  Also see
	    #     http://www.w3.org/TR/html40/struct/objects.html#edef-APPLET
	    # In <applet> tags we must convert the codebase, code, object, and
	    #   archive attributes.
	    # archive here is COMMA-separated list of URI's.
	    # archive, code, and object are all relative to codebase, which
	    #   may be relative to base URL.  Its default is the base URL.
	    #   Note that values of codebase are not supposed to depart from
	    #   dirs and subdirs of the base URL, because of security reasons,
	    #   but some do anyway.  See the above URL for details.
	    # This is untested with real applets.  It *has* been tested to
	    #   ensure that test HTML tags are converted as intended, so any
	    #   applet code that conforms to standards should work.
	    # jsm-- ugh, this seems to fail: some browsers don't handle the
	    #   "code" attribute right if it's an absolute URL.  One
	    #   interpretation of the spec would suggest that maybe setting
	    #   codebase to the nph-proxy.cgi/ path and code to the remainder
	    #   might work... but there may still be problems since the URL
	    #   path doesn't match the class name in the .class file that's
	    #   delivered.

	    } elsif ($tag_name eq 'applet') {
		my($codebase_url)= $attr{codebase} ;

		# Here is where we would guard against codebase leaving the
		#   directory: check for absolute path, absolute URL, or ".." .
		#next if $codebase_url=~ m#^/|^[\w+.-]*:|\.\.# ;

		# if $codebase_url is relative, then make it absolute based on
		#   current $base_ vars.  This is the quick method from full_url().
		# Only do this if $codebase_url is not empty.
		if ($codebase_url ne '') {
		    $codebase_url= 
			  $codebase_url=~ m#^[\w+.-]*:#i ? $codebase_url
			: $codebase_url=~ m#^//#         ? $base_scheme . $codebase_url
			: $codebase_url=~ m#^/#          ? $base_host . $codebase_url
			: $codebase_url=~ m#^\?#         ? $base_file . $codebase_url
			:                                  $base_path . $codebase_url ;
		}

		# codebase must be converted with normal $base_ vars first, but
		#   only after its original value is saved (above).
		$attr{codebase}= &full_url($attr{codebase}), $rebuild=1  if defined($attr{codebase}) ;

		# Use local() copies of $base_ vars, starting with current
		#   values as defaults.
		local($base_url, $base_scheme, $base_host, $base_path, $base_file)=
		    ($base_url, $base_scheme, $base_host, $base_path, $base_file) ;

		# Now set local $base_ vars if needed.
		$base_url= $codebase_url, &fix_base_vars  if $codebase_url ne '' ;

		# These two can now be converted normally, using new $base_ vars.
		$attr{code}=   &full_url($attr{code}),   $rebuild=1  if defined($attr{code}) ;
		$attr{object}= &full_url($attr{object}), $rebuild=1  if defined($attr{object}) ;

		# archive is a comma-separated list of URIs: split, convert, join.
		$attr{archive}= join(',', map {&full_url($_)} split(/\s*,\s*/, $attr{archive})),
		    $rebuild=1  if defined($attr{archive}) ;





	    # <object> tags need special treatment, particularly regarding which
	    #   attributes use which base URIs to resolve them when relative.
	    #   For details, see
	    #     http://www.w3.org/TR/html40/struct/objects.html#edef-OBJECT
	    # The <object> tag has five attributes that may contain URLs to be
	    #   converted:  usemap, codebase, classid, data, archive.  All must
	    #   be converted to absolute URLs, because a browser probably won't
	    #   resolve relative URLs correctly through this proxy.
	    # codebase is used as the base URL for classid, data, and archive;
	    #   it defaults to normal base URI.  In addition, data uses the
	    #   MIME type in "type", and classid uses the MIME type in codetype
	    #   if available, otherwise the one in "type".  Also, all URLs have
	    #   the frame flag set, to avoid inserting a page header into any
	    #   embedded objects (it's legal to embed HTML pages using the
	    #   <object> tag).
	    # The classid attribute is special: it may be a URL, or in MSIE
	    #   it may identify an Active X control by consisting of a unique
	    #   identifier preceded by "clsid:".  For example, MSIE's
	    #   Shockwave Flash player is identified by
	    #   "D27CDB6E-AE6D-11CF-96B8-444553540000".  For each such unique
	    #   object, there are certain <param> tags defined for it.  For
	    #   example, that same ActiveX control requires a <param> tag
	    #   with a name of "movie" and a value equal to the URL where to
	    #   download that movie.  Thus, we need to proxify <param> tags
	    #   with a name of "movie", but only if they're in <object> elements
	    #   with that specific classid.  Thus, we use
	    #   $current_object_classid to keep track of which <object> element
	    #   we're in.  <param> tags are supposed to come before other
	    #   content within <object> elements, so simply remembering the
	    #   classid of the latest <object> tag is sufficient (rather than
	    #   e.g. storing a stack of classids of nested objects).
	    # Several places here, we use local copies of the $base_ vars and
	    #   $url_start to call full_url() with desired base URLs, types, etc.
	    # There are a few sites with embedded objects or applets that may not
	    #   work if the proxy_encode() routine is not the simple default.  See
	    #   the comments above that routine for details.  It has to do with
	    #   the objects trying to resolve relative URLs.

	    } elsif ($tag_name eq 'object') {
		# Set $current_object_classid for detailed <param> handling
		$current_object_classid= $attr{classid} ;

		# Verify that $attr{type} is a valid MIME type.
		($attr{type})= $attr{type}=~ m#^\s*([\w.+\$-]*/[\w.+\$-]*)#, $rebuild=1
		    if  defined($attr{type}) && $attr{type}!~ m#^[\w.+\$-]+/[\w.+\$-]+$# ;

		# Verify that $attr{codetype} is a valid MIME type.
		($attr{codetype})= $attr{codetype}=~ m#^\s*([\w.+\$-]*/[\w.+\$-]*)#, $rebuild=1
		    if  defined($attr{codetype}) && $attr{codetype}!~ m#^[\w.+\$-]+/[\w.+\$-]+$# ;

		my($type)=     lc($attr{type}) ;
		my($codetype)= lc($attr{codetype}) ;
		my($codebase_url)= $attr{codebase} ;

		# Remove tag if it links to a script type and scripts are banned.
		# Check both type and codetype.
		next if $scripts_are_banned_here &&
		    (   $type=~     /^$SCRIPT_TYPE_REGEX$/io
		     || $codetype=~ /^$SCRIPT_TYPE_REGEX$/io ) ;

		# if $codebase_url is relative, then make it absolute based on
		#   current $base_ vars.  This is the quick method from full_url().
		# Only do this if $codebase_url is not empty.
		if ($codebase_url ne '') {
		    $codebase_url= 
			  $codebase_url=~ m#^[\w+.-]*:#i ? $codebase_url
			: $codebase_url=~ m#^//#         ? $base_scheme . $codebase_url
			: $codebase_url=~ m#^/#          ? $base_host . $codebase_url
			: $codebase_url=~ m#^\?#          ? $base_file . $codebase_url
			:                                  $base_path . $codebase_url ;
		}

		# usemap is the only attribute converted normally.
		$attr{usemap}= &full_url($attr{usemap}), $rebuild=1  if defined($attr{usemap}) ;

		# codebase must be converted with normal $base_ vars first, but
		#   only after its original value is saved (above).
		$attr{codebase}= &full_url_by_frame($attr{codebase},1), $rebuild=1
		    if defined($attr{codebase}) ;

		# For remaining three attributes, use $base_ vars according to
		#   $codebase_url, without which default to original $base_ vars.
		local($base_url, $base_scheme, $base_host, $base_path, $base_file)=
		    ($base_url, $base_scheme, $base_host, $base_path, $base_file) ;
		$base_url= $codebase_url, &fix_base_vars  if $codebase_url ne '' ;

		# archive is a space-separated list of URIs: split, convert, join.
		# Do this before changing $url_start for data and classid handling.
		$attr{archive}= join(' ', map {&full_url_by_frame($_,1)} split(" ", $attr{archive})),
		    $rebuild=1  if defined($attr{archive}) ;

		# Convert data attribute if needed.
		# Note that $is_in_frame is set to 1 anyway, so go ahead and
		#   generate a new $url_start regardless.
		if (defined($attr{data})) {
		    local($url_start)= $script_url . '/' .
			&pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
				    $e_hide_referer, $e_insert_entry_form, 1, $type)
			. '/' ;
		    $attr{data}= &full_url($attr{data}) ;
		    $rebuild= 1 ;
		}


		# Convert classid attribute if needed.
		# Special case: Don't convert classid if it begins with
		#   "clsid:".  "clsid:" is a non-standard URL scheme that
		#   indicates the "UUID" of an object, and is sometimes used
		#   with embedded objects like Flash, etc.  It is described in
		#   a 1996 draft at http://www.w3.org/Addressing/clsid-scheme .

		if (defined($attr{classid}) && ($attr{classid}!~ /^clsid:/i)) {
		    local($url_start)= $script_url . '/' .
			&pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
				    $e_hide_referer, $e_insert_entry_form, 1,
				    ($codetype ne '')   ? $codetype   : $type )
			. '/' ;
		    $attr{classid}= &full_url($attr{classid}) ;
		    $rebuild= 1 ;
		}

		# Proxifying SWF files relies on our JS library.
		$needs_jslib= 1 ;





	    # This will likely only be used when called recursively by the
	    #   block below that handles <script>...<script> blocks.

	    } elsif ($tag_name eq 'script') {

		# Probably won't get here, but catch in case one slips through.
		next if $scripts_are_banned_here ;

		# Verify that $attr{type} is a valid MIME type.
		($attr{type})= $attr{type}=~ m#^\s*([\w.+\$-]*/[\w.+\$-]*)#, $rebuild=1
		    if  defined($attr{type}) && $attr{type}!~ m#^[\w.+\$-]+/[\w.+\$-]+$# ;

		# Netscape apparently trusts expected type here, including the
		#   default to JavaScript, and completely ignores the Content-Type:
		#   header. The expected type first comes from "type" attribute,
		#   else "language" attribute, else default.
		# Konqueror, on the other hand, treats all external scripts as
		#   JavaScript, regardless of either expected type or Content-Type: .
		# Set the expected type in the URL flags, and the resource will be
		#   interpreted appropriately when downloaded in e.g. http_get().

		if (defined($attr{src})) {
		    my($type, $language) ;

		    $type= lc($attr{type}) ;

		    # If there's no type, but there's a language attribute, then
		    #   use that instead to guess the expected type.
		    if (!$type && ($language= $attr{language})) {
			$type= $language=~ /javascript|ecmascript|livescript|jscript/i
							 ? 'application/x-javascript'
			     : $language=~ /css/i        ? 'text/css'
			     : $language=~ /vbscript/i   ? 'application/x-vbscript'
			     : $language=~ /perl/i       ? 'application/x-perlscript'
			     : $language=~ /tcl/i        ? 'text/tcl'
			     :                             ''
		    }
		    $type||= $default_script_type ;

		    # Use a local copy of $url_start to call full_url() normally.
		    # Only generate new $url_start if the type flag has changed.
		    local($url_start)= $url_start ;
		    if ($type) {
			$url_start= $script_url . '/' .
			    &pack_flags($e_remove_cookies, $e_remove_scripts,
					$e_filter_ads, $e_hide_referer,
					$e_insert_entry_form, $is_in_frame, $type)
			    . '/' ;
		    }
		    $attr{src}= &full_url($attr{src}) ;
		    $rebuild= 1 ;

		    # Set $needs_jslib if we're loading an external JavaScript resource.
		    # If $type is empty, then check $default_script_type instead.
		    $needs_jslib= 1
			if ($type || $default_script_type)=~
			    m#^(?:application/x-javascript|application/x-ecmascript|application/javascript|application/ecmascript|text/javascript|text/ecmascript|text/livescript|text/jscript)$#i ;
		}



	    # This will likely only be used when called recursively by the
	    #   block below that handles <style>...<style> blocks.

	    } elsif ($tag_name eq 'style') {
		# Verify that $attr{type} is a valid MIME type.
		($attr{type})= $attr{type}=~ m#^\s*([\w.+\$-]*/[\w.+\$-]*)#, $rebuild=1
		    if  defined($attr{type}) && $attr{type}!~ m#^[\w.+\$-]+/[\w.+\$-]+$# ;





	    # These are seldom-used tags, or tags that seldom have URLs in them

	    } elsif ($tag_name eq 'select') {     # HTML 3.0
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'hr') {         # HTML 3.0
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'td') {         # Netscape extension?
		$attr{background}= &full_url($attr{background}), $rebuild=1 if defined($attr{background}) ;

	    } elsif ($tag_name eq 'th') {         # Netscape extension?
		$attr{background}= &full_url($attr{background}), $rebuild=1 if defined($attr{background}) ;

	    } elsif ($tag_name eq 'tr') {         # Netscape extension?
		$attr{background}= &full_url($attr{background}), $rebuild=1 if defined($attr{background}) ;

	    } elsif ($tag_name eq 'table') {      # Netscape extension?
		$attr{background}= &full_url($attr{background}), $rebuild=1 if defined($attr{background}) ;

	    } elsif ($tag_name eq 'bgsound') {    # Microsoft only
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'blockquote') {
		$attr{cite}= &full_url($attr{cite}), $rebuild=1  if defined($attr{cite}) ;

	    } elsif ($tag_name eq 'del') {
		$attr{cite}= &full_url($attr{cite}), $rebuild=1  if defined($attr{cite}) ;

	    } elsif ($tag_name eq 'embed') {      # Netscape only
		next if $scripts_are_banned_here
		     && $attr{type}=~ /^$SCRIPT_TYPE_REGEX$/io ;

		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;
		$attr{pluginspage}= &full_url($attr{pluginspage}),  $rebuild=1  if defined($attr{pluginspage}) ;

		$attr{flashvars}=  &proxify_flashvars($attr{flashvars}),  $rebuild=1  if defined($attr{flashvars}) ;

		# Convert data attribute if needed.
		# Note that $is_in_frame is set to 1 anyway, so go ahead and
		#   generate a new $url_start regardless.
		if (defined($attr{data})) {
		    local($url_start)= $script_url . '/' .
			&pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
				    $e_hide_referer, $e_insert_entry_form, 1, $attr{type})
			. '/' ;
		    $attr{data}= &full_url($attr{data}) ;
		    $rebuild= 1 ;
		}

		# Proxifying SWF files relies on our JS library.
		$needs_jslib= 1 ;


	    } elsif ($tag_name eq 'fig') {        # HTML 3.0
		$attr{src}=      &full_url($attr{src}),      $rebuild=1  if defined($attr{src}) ;
		$attr{imagemap}= &full_url($attr{imagemap}), $rebuild=1  if defined($attr{imagemap}) ;

	    } elsif ($tag_name=~ /^h[1-6]$/) {    # HTML 3.0
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'ilayer') {
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'ins') {
		$attr{cite}= &full_url($attr{cite}), $rebuild=1  if defined($attr{cite}) ;

	    } elsif ($tag_name eq 'note') {       # HTML 3.0
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'overlay') {    # HTML 3.0
		$attr{src}=      &full_url($attr{src}),      $rebuild=1  if defined($attr{src}) ;
		$attr{imagemap}= &full_url($attr{imagemap}), $rebuild=1  if defined($attr{imagemap}) ;

	    } elsif ($tag_name eq 'q') {
		$attr{cite}= &full_url($attr{cite}), $rebuild=1  if defined($attr{cite}) ;

	    } elsif ($tag_name eq 'ul') {         # HTML 3.0
		$attr{src}=  &full_url($attr{src}),  $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'video') {      # HTML 5
		$attr{src}=     &full_url($attr{src}),     $rebuild=1  if defined($attr{src}) ;
		$attr{poster}=  &full_url($attr{poster}),  $rebuild=1  if defined($attr{poster}) ;

	    } elsif ($tag_name eq 'audio') {      # HTML 5
		$attr{src}=     &full_url($attr{src}),     $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'track') {      # HTML 5
		$attr{src}=     &full_url($attr{src}),     $rebuild=1  if defined($attr{src}) ;

	    } elsif ($tag_name eq 'source') {     # HTML 5
		$attr{src}=     &full_url($attr{src}),     $rebuild=1  if defined($attr{src}) ;



	    }   #####   END OF TAG-SPECIFIC PROCESSING   #####



	    # We must make sure every iframe without a URL gets the JavaScript library.
	    #   This is tricky and messy.  To do it, we add a <script> block after the
	    #   <iframe> tag.
	    my($iframe_jslib, $iframe_id) ;
	    if ($tag_name eq 'iframe' and ($attr{src}=~ /^about:blank$/i or $attr{src} eq '')) {
		if (!defined $attr{id} or $attr{id} eq '') {
		    $iframe_id= random_string(10) ;
		    $attr{id}= $iframe_id ;
		    $rebuild= 1 ;
		} else {
		    $rebuild= 1  if $attr{id}=~ s/\W//g ;
		    $iframe_id= $attr{id} ;
		}
		my $dummy_iframe_id= random_string(10) ;

		# Awkwardly, we must close the <iframe> element before our script, and
		#   append a dummy "<iframe>" tag to handle the original closing </iframe> .
		$iframe_jslib= <<EOT ;
</iframe><script>
_proxy_jslib_init_iframe(document.getElementById('$iframe_id')) ;
</script><iframe id="$dummy_iframe_id">
EOT
	    }


	    # Rebuild the tag if it has been changed, as fast as possible.
	    # Attributes with value of '' are added without a value, like "selected".
	    # Undefined attributes are removed.
	    # Otherwise, use single quotes only if the values contain double
	    #   quotes and no single quotes, else use double quotes.  This
	    #   handles script-type attributes most cleanly.
	    # This is a bottleneck of the script, done for every rebuilt tag.
	    # The functionality of HTMLescape() is inlined here for speed.

	    if ($rebuild) {
		my($name, $value, $attrs, $end_slash) ;

		while (($name, $value)= each %attr) {
		    next unless defined($value) ;

		    # This makes strict XHTML fail, so let it fall through to
		    #   e.g. 'checked=""'; does that work for all cases?
		    #$attrs.= (' ' . $name), next   if $value eq '' ;

		    $value=~ s/&/&amp;/g ;
		    $value=~ s/([\x00-\x1f\x7f])/'&#' . ord($1) . ';'/ge ;
		    $value=~ s/</&lt;/g ;
		    $value=~ s/>/&gt;/g ;
		    if ($value!~ /"/ || $value=~ /'/) {
			$value=~ s/"/&quot;/g ;  # only needed when using double quotes
			$attrs.= join('', ' ', $name, '="', $value, '"') ;
		    } else {
			$attrs.= join('', ' ', $name, "='", $value, "'") ;
		    }
		}

		$end_slash= $tag=~ m#/\s*>?$#   ? ' /'   : '' ;
		$tag= "<$tag_name$attrs$end_slash>$iframe_jslib" ;
	    }

	    push(@out, $tag) ;





	# $tag processing done.  Now, handle the other main cases-- comments,
	#   <script> blocks, <style> blocks, and <!...> declarations.


	# Handle comments of both the <!--...--> and <!--...> varieties.
	} elsif ($comment) {

	    # Handle "conditional comments", which begin with "<!--&{" and
	    #   end with "};".  They evaluate the initial expression, and
	    #   depending on that, include or exclude the rest of the comment.
	    if ( $comment=~ /^<!--\s*&{/ ) {

		# Remove the whole conditional comment if scripts are banned.
		next if $scripts_are_banned_here ;  # remove it by not doing push(@out)

		# Otherwise, proxify conditional comments as configured.  Proxify
		#   the HTML content in any case, since it could get rendered.
		my($condition, $contents, $end)=
		    $comment=~ /^<!--\s*&{(.*?)}\s*;(.*?)(--\s*)?>$/s ;
		$condition= (&proxify_block($condition, $default_script_type))[0]
		    if $PROXIFY_SCRIPTS ;
		$contents=  &proxify_html(\$contents, 0, $no_exit_on_frameset) ;
		$comment= join('', '<!--&{', $condition, '};', $contents, $end, '>') ;


	    # Handle MSIE's form of "conditional comments", which are cruder and
	    #   use a different syntax-- they are either
	    #     <!--[if ...]>...<![endif]-->     or
	    #     <![if ! ...]>...<![endif]>
	    # We can ignore the second form; they will be handled already.
	    # There may also be something like "<!--[if ...]><!--> ... <!--<![endif]-->",
	    #   so handle that too.
	    } elsif ( $comment=~ /^<!--\s*\[\s*if\b/i ) {

		# Proxify the contents of the comment.
		my($start, $contents, $end)=
		    $comment=~ /^(<!--[^>]*?>)(.*?)(<!\s*(?:\[\s*endif|--)[^>]*?>)$/is ;
		$contents=  &proxify_html(\$contents, 0, 1) ;
		$comment= "$start$contents$end" ;


	    # Otherwise, for normal comments, proxify them if so configured.
	    # Note that here, we don't want to exit on a <frameset> tag, so
	    #   set the third parameter to proxify_html().
	    } elsif ($PROXIFY_COMMENTS) {
		my($contents, $end)= $comment=~ /^<!--(.*?)(--\s*)?>$/s ;
		$contents=  &proxify_html(\$contents, 0, 1) ;
		$comment= "<!--$contents$end>" ;
	    }

	    push(@out, $comment) ;




	# Handle <script> blocks, meaning either removal, or proxifying the
	#   <script> tag and/or the script content as needed.
	# NOTE: IF YOU MODIFY THIS BLOCK, then be sure to review and possibly
	#   modify the corresponding routine _proxy_jslib_proxify_script_block() in the
	#   JavaScript library, far below in the routine return_jslib().  It is
	#   a Perl-to-JavaScript translation of this block.
	} elsif ($script_block) {
	    my($tag, $script, $attrs, %attr, $type, $language, $name, $remainder) ;

	    # If needed, remove script altogether by not doing push(@out).
	    next if $scripts_are_banned_here ;

	    # Parse the <script> block.
	    ($tag, $script)=
		$script_block=~ m#^(<\s*script\b[^>]*>)(.*)<\s*/script\b.*?>\z#si ;

	    # Proxify <script> tag itself by calling proxify_html() on it.
	    # There is a block in the "if ($tag)" block above that handles
	    #   <script> tags and all relevant attributes in them.  This
	    #   includes fixing the type attribute if needed.
	    $tag= &proxify_html(\$tag, 0) ;

	    # Extract attributes into %attr.
	    # Regex below must be in scalar context for /g to work.
	    ($attrs)= $tag=~ /^<\s*script\b([^>]*)>/i ;
	    while ($attrs=~ /([A-Za-z][\w.:-]*)\s*(?:=\s*(?:"([^">]*)"?|'([^'>]*)'?|([^'"][^\s>]*)))?/g ) {
		$name= lc($1) ;
		next if exists($attr{$name}) ;   # duplicate attr
		$attr{$name}= &HTMLunescape(defined($2) ? $2
					  : defined($3) ? $3
					  : defined($4) ? $4
					  : '' ) ;
	    }

	    # Find script's MIME type: use type attribute if available,
	    #   else guess from language attribute, else use default
	    #   script type (even though it's not legal HTML).  See notes in
	    #   <script>-handling block far above, in "if ($tag)" block.
	    $type= lc($attr{type}) ;
	    if (!$type && ($language= $attr{language})) {
		$type= $language=~ /javascript|ecmascript|livescript|jscript/i
						 ? 'application/x-javascript'
		     : $language=~ /css/i        ? 'text/css'
		     : $language=~ /vbscript/i   ? 'application/x-vbscript'
		     : $language=~ /perl/i       ? 'application/x-perlscript'
		     : $language=~ /tcl/i        ? 'text/tcl'
		     :                             ''
	    }
	    $type||= $default_script_type ;


	    # Proxify the script content if needed.
	    # If JS content (erroneously) contains the string "</script" (e.g. in
	    #   a string literal), then append to it everything up to the next
	    #   "</script".  Repeat as necessary.  Note that this affects
	    #   pos($$body_ref), the only place other than the main loop
	    #   condition to do so.
	    # When appending, use the correct "<\/script" instead of "</script".
	    #   Oddly, browsers (Firefox and Konqueror) seem to allow "</script" in
	    #   a string only when it's in a document.write() statement.  Thus,
	    #   without the "\", browsers would end the <script> on the "</script"
	    #   in our modified JS.
	    # All this requires first parsing the <script> element, calculating
	    #   its MIME type, and finding $remainder, unfortunately, even if
	    #   we're just removing scripts.
	    # Currently, we only detect premature "</script" strings for
	    #   JavaScript scripts.
	    # jsm-- this may not work when $PROXIFY_SCRIPTS==0 .  The solution
	    #   would require tokenizing $script, just to test for an
	    #   unterminated string.
	    if ($type=~ m#^(application/x-javascript|application/x-ecmascript|application/javascript|application/ecmascript|text/javascript|text/ecmascript|text/livescript|text/jscript)$#i) {
		my($new_script)= $script ;
		while ($PROXIFY_SCRIPTS) {
		    # get_string_literal_remainder() (which is indirectly
		    #   called by proxify_block() ) may throw an "end_of_input\n"
		    #   error (via a "die" statement), which signals to us that
		    #   the string "</script" was in a JavaScript string
		    #   literal, i.e. that we need to append the script block
		    #   with everything up to the next "</script>" in the input
		    #   stream.
		    # Note that the error string has to end with "\n" because
		    #   of the nature of "die" statements.
		    # Browsers seem to fully ignore script blocks with
		    #   unterminated string literals, so we do that too.  Other
		    #   syntax errors stop JS processing completely, so don't
		    #   just return partially proxified script.
		    eval { $new_script= (&proxify_block($script, $type))[0] } ;
		    last unless $@ ;
		    if ($@ eq "end_of_input\n") {
			my($more)= $$body_ref=~ m#\G(.*?)<\s*/script\b.*?>#sgci ;
			$new_script= '', last unless $more ;
			$script.= "<\\/script>" . $more ;
		    } else {
			die $@ ;    # pass through any other error
		    }
		}
		$script= $new_script ;
	    }

	    push(@out, $tag, $script, '</script>') ;




	# Handle <style> blocks.
	# NOTE: IF YOU MODIFY THIS BLOCK, then be sure to review and possibly
	#   modify the corresponding routine _proxy_jslib_proxify_style_block() in the
	#   JavaScript library, far below in the routine return_jslib().  It is
	#   a Perl-to-JavaScript translation of this block.
	} elsif ($style_block) {
	    my($tag, $attrs, $stylesheet, $type) ;

	    ($tag, $stylesheet)=
		$style_block=~ m#^(<\s*style\b[^>]*>)(.*?)<\s*/style\b.*?>#si ;

	    # Proxify <style> tag itself by calling proxify_html() on it.
	    # This includes fixing the type attribute if needed.
	    $tag= &proxify_html(\$tag, 0) ;

	    # Abbreviated attribute extraction, only to find $type.
	    # Regex below must be in scalar context for /g to work.
	    ($attrs)= $tag=~ /^<\s*style\b([^>]*)>/ ;
	    while ($attrs=~ /([A-Za-z][\w.:-]*)\s*(?:=\s*(?:"([^">]*)"?|'([^'>]*)'?|([^'"][^\s>]*)))?/g ) {
		$type= lc(&HTMLunescape(defined($2) ? $2
				      : defined($3) ? $3
				      : defined($4) ? $4
				      : '' )), last
		    if lc($1) eq 'type' ;
	    }

	    $type||= $default_style_type ;

	    # Remove stylesheet if it's a script type and scripts are banned.
	    next if $scripts_are_banned_here && $type=~ /^$SCRIPT_TYPE_REGEX$/io ;

	    # Proxify the stylesheet.
	    $stylesheet= (&proxify_block($stylesheet, $type))[0] ;

	    push(@out, $tag, $stylesheet, '</style>') ;




	# Handle any <!...> declarations.
	# Declarations can contain URLs, such as for DTD's.  Most legitimate
	#   declarations would be safe if left unconverted, but if we don't
	#   convert URLs then a malicious document could use this mechanism
	#   to break privacy.  Here we use a simple method to handle virtually
	#   all existing cases and close all privacy holes.
	} elsif ($decl_bang) {
	    my($inside, @words, $q, $rebuild) ;
	    ($inside)= $decl_bang=~ /^<!([^>]*)/ ;
	    @words= $inside=~ /\s*("[^">]*"?|'[^'>]*'?|[^'"][^\s>]*)/g ;

	    # Instead of handling all SGML declarations, the quick hack here is
	    #   to convert any "word" in it that looks like an absolute URL.  It
	    #   handles virtually all existing cases well enough, and closes any
	    #   privacy hole regardless of the declaration.
	    foreach (@words) {
		# Don't hammer on W3C's poor servers.
		next if m#^['"]?http://www\.w3\.org/#i ;

		if (m#^["']?[\w+.-]+://#) {
		    if    (/^"/)  { $q= '"' ; s/^"|"$//g }
		    elsif (/^'/)  { $q= "'" ; s/^'|'$//g }
		    else          { $q= '' }

		    $_= $q . &HTMLescape(&full_url(&HTMLunescape($_))) . $q ;
		    $rebuild= 1 ;
		}
	    }

	    $decl_bang= '<!' . join(' ', @words) . '>'   if $rebuild ;

	    push(@out, $decl_bang) ;




	# Handle any <?...?> declarations, such as XML declarations.
	} elsif ($decl_question) {

	    # Nothing needs to be done to these.
	    push(@out, $decl_question) ;




	}  # end of main if comment/script/style/declaration/tag block


    } continue {
	$first_script_pos= $out_start
	    if $needs_jslib && !defined($first_script_pos) ;

    }  # end of main while loop



    #   @out now has proxified HTML


    # Finally, a few things might be inserted into the page, if we're proxifying
    #   a full page and not just an HTML fragment.
    if ($is_full_page) {

	# Inserting anything (even a comment) before initial <!...> or <?...?>
	#   declarations confuses some browsers (like MSIE 6.0), so any
	#   insertion should go after initial declarations.  Thus, find
	#   the point right after any such declarations.
	# Note that comments may be included in an XML prolog, so they're
	#   matched here too.
	my($after_decl, $i) ;
	for ($i= 0; $i<@out; $i++) {
	    next unless $out[$i]=~ /^</ ;
	    $after_decl= $i+1, next if $out[$i]=~ /^<\s*(?:\?|!)/ ;
	    last ;   # if it's any other tag
	}


	# Insert form and/or other header as needed, if we're not in a frame.
	# Insert it right after the <body> tag if available, else right after
	#   the <html> tag, else at the beginning.
	# Don't insert anything if there was no (non-whitespace) content, or
	#   else <frameset> tags won't work.
	splice(@out, ($body_pos || $html_pos || $after_decl), 0, $full_insertion)
	    if $doing_insert_here && $has_content ;


	# If needed, insert <script src="...//scripts/jslib"> element to load
	#   the JavaScript library.  Put it right after the <head> tag if
	#   available, else right after the <html> tag, else at the beginning.
	# Also call _proxy_jslib_pass_vars().  It is a general mechanism to
	#   pass any needed values into the JS library.  As this script changes,
	#   this call to _proxy_jslib_pass_vars() may have new arguments added.
	#   Feel free to add your own arguments as needed to communicate from
	#   this Perl script to the JS library as it runs in the browser.  Be
	#   sure to update the _proxy_jslib_pass_vars() routine in the JS
	#   library, far below.
	# Set the base URL via a parameter to _proxy_jslib_pass_vars().  We
	#   don't track the base URL with every <base> tag like we do in the
	#   main body of this script; we just use the final base URL (which is
	#   like some browsers; see comments in proxify_html() by the <base> tag
	#   section for details).  To set it with every <base> tag would get
	#   messy, because proxify_html() also works on HTML fragments and
	#   doesn't know whether the enclosing page will use JS, and we don't
	#   want to insert unneeded JS.  This only matters for erroneous HTML
	#   anyway, because no more than one <base> tag is allowed; no privacy
	#   holes are opened or anything like that.
	# This won't work with the splice() just above if $body_pos is less than
	#   $head_pos.  That's invalid HTML, but if we ever need to handle it,
	#   then adjust $head_pos with the splice() above.
	# $needs_jslib is set when certain JavaScript is proxified in
	#   proxify_js(), or if an external (JavaScript) script is loaded with
	#   <script src=...>.  Conceivably, an external stylesheet could
	#   require the library too, but not likely.  We can fix that if
	#   needed.  Same for embedded objects that are script types.
	# Some pages might have script content before the <head> block, or
	#   otherwise placed illegally.  For this, we keep track of
	#   $first_script_pos, a slightly messy solution.
	# Brain-dead MSIE doesn't recognize "application/x-javascript", which
	#   is the only strictly correct MIME type for JavaScript.  Thus, we
	#   use the common and MSIE-recognized alternate, "text/javascript".
	if ($PROXIFY_SCRIPTS && $needs_jslib) {
	    my($jslib_block)= &js_insertion() ;
	    my($insert_pos)= $head_pos || $html_pos || $after_decl ;
	    $insert_pos= $first_script_pos
		if defined($first_script_pos) && $first_script_pos<$insert_pos ;
	    splice(@out, $insert_pos, 0, $jslib_block) ;
	}

	# This causes more trouble than it's worth, e.g. when XMLHttpRequest
	#   returns a string that is then tested, but fails because this is
	#   inserted.  So let's remove it.
	## Prepend newline if it's after any declarations.
	#splice(@out, $after_decl, 0, ($after_decl ? "\n" : ''),
	#       "<!-- resource has been modified by proxy -->\n") ;

    }


    return join('', @out) ;

}  # sub proxify_html()



# Very similar to proxify_html(), except that the unparsed remainder is
#   returned along with the proxified HTML.  See proxify_html for comments.
#   This routine is intended to proxify pieces of HTML, and thus we can't
#   assume it's a full page being proxified.  Thus, for example, comments
#   have to be matched differently from the way they are in proxify_html().
# This isn't the most efficient, as it merely calls proxify_html() (and thus
#   the HTML is parsed twice), but this routine is only used in rare situations.
# There are two things to insert into a page: the URL form insertion plus any
#   user insertion goes into <body>, and the JavaScript insertion goes into
#   <head>.  Here we assume the HTML is correct, and there is exactly one
#   <head> element and one <body> element.  Invalid HTML is not handled.  The
#   result is that an invalid page will fail, but it won't be a privacy hole.
sub proxify_html_part {
    my($body_ref)= @_ ;
    my(@out, $block) ;

    # We don't need to distinguish among block types in this simple routine.
    # We do need to exclude lone <script> and <style> tags from matching.
    # Note that the scheme for matching comments in proxify_html() won't work
    #   here, so we just end them on "-->".  Not perfect, but will only be
    #   used for those pages that require this routine.
    while ( $$body_ref=~ m{\G([^<]*
			      (?:<!--.*?--\s*>
				|<\s*script\b.*?<\s*/script\b.*?>
				|<\s*style\b.*?<\s*/style\b.*?>
				|<!(?!--)[^>]*>
				|<\?[^>]*>
				|<\s*(?!script\b|style\b|!)[^>]*>
			      )
			   )
			  }sgcix )
    {
	$block= $1 ;

	push(@out, &proxify_html(\$block)) ;
	push(@out, &js_insertion())          if $block=~ /^[^<]*<\s*head\b/i ;
	push(@out, &full_insertion($URL,0))  if $block=~ /^[^<]*<\s*body\b/i ;
    }

    return ( join('', @out), substr($$body_ref, pos($$body_ref)) ) ;
}



# This is used when the current URL matches a pattern in
#   @TRANSMIT_HTML_IN_PARTS_URLS .  It contains elements of http_get().
# The output response may be chunked, even if the input response is not.
# $headers is printed here, since it may be modified here.
sub transmit_html_in_parts {
    my($headers, $S)= @_ ;
    my($buf, $length, $numread, $thisread, $out) ;

    # Handle chunked response
    if ($headers=~ /^Transfer-Encoding:[ \t]*chunked\b/mi) {
	my($chunk_size, $chunk, $footers) ;

	print $STDOUT $headers ;

	while ($chunk_size= hex(<$S>) ) {
	    $buf.= $chunk= &read_socket($S, $chunk_size) ;
	    return undef unless length($chunk) == $chunk_size ;
	    $_= <$S> ;         # clear CRLF after chunk
	    ($out, $buf)= &proxify_html_part(\$buf) ;
	    print $STDOUT sprintf('%x', length($out)), "\015\012", $out, "\015\012"
		if $out ne '' ;
	}
	# Print any remaining buffer, and the end of the chunks.
	print $STDOUT sprintf('%x', length($buf)), "\015\012", $buf, "\015\012"
	    if $buf ne '' ;
	print $STDOUT "0\015\012" ;

	# After all chunks, read any footers, including the final blank line.
	while (<$S>) {
	    $footers.= $_ ;
	    last if /^(\015\012|\012)/  || $_ eq '' ;  # lines end w/ LF or CRLF
	}
	$footers=~ s/(\015\012|\012)[ \t]+/ /g ;       # unwrap long footer lines
	print $STDOUT $footers ;


    # Handle explicitly sized response.  Since we can't support
    #   the Content-Length: header, return chunked response.
    } elsif ($headers=~ /^Content-Length:[ \t]*(\d+)/mi) {
	$length= $1 ;

	# Change from specified-length to chunked encoding.
	$headers=~ s/^Content-Length:.*/Transfer-Encoding: chunked\015/mi ;

	print $STDOUT $headers ;

	# Read a block at a time, and write any available output as a chunk.
	while (    ($numread<$length)
		&& ($thisread= read($S, $buf, $length-$numread, length($buf)) ) )
	{
	    return undef unless defined($thisread) ;
	    $numread+= $thisread ;
	    ($out, $buf)= &proxify_html_part(\$buf) ;
	    print $STDOUT sprintf('%x', length($out)), "\015\012", $out, "\015\012"
		if $out ne '' ;
	}
	# Print any remaining buffer, and the end of the chunked response.
	print $STDOUT sprintf('%x', length($buf)), "\015\012", $buf, "\015\012"
	    if $buf ne '' ;
	print $STDOUT "0\015\012\015\012" ;   # no footers


    # Handle unsized response.
    } else {
	local($/)= '>' ;
	print $STDOUT $headers ;
	while (<$S>) {
	    last if $_ eq '' ;
	    $buf.= $_ ;
	    ($out, $buf)= &proxify_html_part(\$buf) ;
	    print $STDOUT $out ;
	}
	return undef unless defined($thisread) ;
	print $STDOUT $buf ;
    }
}



#--------------------------------------------------------------------------


# Returns the full absolute URL to query our script for the given URI
#   reference.  PATH_INFO will include the encoded absolute URL of the target,
#   but the fragment will be appended unencoded so browsers will resolve it
#   correctly.
# If $retain_query is set, then the query string is removed before proxifying,
#   then readded at the end.  This is required for e.g. Flash apps, which
#   read any query parameters into program variables, and thus the query
#   string must be retained.  The downside of this is that the query string
#   is not encoded for such URLs, possibly reducing privacy.  The "real"
#   solution might be to rewrite the Flash proxification to parse the query
#   string out of document.URL and set those program variables initially.
#   We may do this at some point.  A broader solution would be to set up
#   general handlers similar to _proxy_jslib_handle() and _proxy_jslib_assign()
#   in the SWF library, to be called instead of every getMember and setMember
#   action; maybe we can get away without doing that, since that might slow
#   down Flash apps considerably.  We'll see.
# If a "javascript:" URL is in e.g. a "src" attribute, then the result of the
#   last JS statement becomes the contents of that element.  Thus, the last
#   statement needs to be wrapped in "_proxy_jslib_proxify_html(...)".  Since
#   there may be multiple statements in the URL, separated by semicolons, we
#   need to use separate_last_js_statement().
# This is a major bottleneck for the whole program, so speed is important here.
# Note that the calculations of $url_start, $base_scheme, $base_host, 
#   $base_path, and $base_file throughout the program are an integral part of
#   this routine, placed elsewhere for speed.
# For HTTP, The URL to be encoded should include everything that is sent in
#   the request, including any query, but not any fragment.
# This only returns absolute URLs, though relative URLs would usually suffice.
#   If it matters, we could have a fullrelurl() and fullabsurl(), the latter
#   used for those HTML attributes that require an absolute URL (like <base>).
#
# The ?:?:?: statement resolves relative URLs to absolute URLs, given the
#   $base_{url,scheme,host,path} variables figured earlier.  It does it
#   simply and efficiently, and accurately enough; the full procedure is
#   described in RFC 2396 (URI syntax), section 5.2.
# RFC 2396, section 5 states that there are three types of relative URIs:
#   net_path (beginning with //, rarely used), abs_path (beginning with /),
#   and rel_path, any of which may be followed by a "?query"; the query must
#   be included in the result.  Thus, we only need to examine the start of
#   the relative URL.
# This ?:?:?: statement passes all test cases in RFC 2396 appendix C, except
#   for the following:  It does not reduce . and .. path segments (to do
#   so would take a lot more time), and it assumes $uri_ref has something
#   other than an empty fragment in it, i.e. that the URI is non-empty.
# This only works for hierarchical schemes, like HTTP or FTP.  Conceivably,
#   there's a problem if the base URL uses a non-hierarchical scheme, and
#   the document contains relative URLs.  Absolute URLs will be OK.
# Any HTML-escaping/unescaping should be done outside of this routine, since
#   it is used for any relative->absolute URL conversion, not just HTML.
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_full_url() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of this routine.

sub full_url {
    my($uri_ref, $retain_query)= @_ ;

    # Disable $retain_query until potential anonymity issues are resolved.
    $retain_query= 0 ;

    $uri_ref=~ s/^\s+|\s+$//g ;  # remove leading/trailing whitespace

    return $uri_ref if ($uri_ref=~ /^about:\s*blank$/i) ;

    # For now, prevent redirecting into x-proxy URLs.
    return undef if $uri_ref=~ m#^x-proxy:#i ;

    # Handle "javascript:" URLs separately.  "livescript:" is an old synonym.
    if ($uri_ref=~ /^(?:javascript|livescript):/i) {
	return undef if $scripts_are_banned_here ;
	return $uri_ref unless $PROXIFY_SCRIPTS ;
	my($script)= $uri_ref=~ /^(?:javascript|livescript):(.*)$/si ;
	my($rest, $last)= &separate_last_js_statement(\$script) ;
	$last=~ s/\s*;\s*$// ;
	return 'javascript:' . (&proxify_js($rest, 1))[0]
			     . '; _proxy_jslib_proxify_html(' . (&proxify_js($last, 0))[0] . ')[0]' ;
    }

    # Handle "data:" URIs specially.  They include a resource's entire data in a URL.
    if ($uri_ref=~ /^data:/i) {
	my($type, $clauses, $content)= $uri_ref=~ m#^data:([\w.+\$-]+/[\w.+\$-]+)?;?([^,]*),?(.*)#is ;
	$type= lc($type) ;
	if ($type eq 'text/html' or $type=~ /^$TYPES_TO_HANDLE_REGEX$/io) {
	    my($data_charset, $base64) ;
	    for (split(/;/, $clauses)) {
		$data_charset= $1, next  if /^charset=(\S+)/i ;
		$base64= 1  if lc eq 'base64' ;
	    }
	    if ($base64) {
		$content= unbase64($content) ;
	    } else {
		$content=~ s/%([\da-fA-F]{2})/ chr(hex($1)) /ge ;
	    }
	    if ($data_charset) {
		eval { $content= decode($data_charset, $content) } ;
		&malformed_unicode_die($data_charset) if $@ ;
	    }
	    $content= ($type eq 'text/html')  ? proxify_html($content)  : proxify_block($content, $type) ;
	    $content= encode($data_charset, $content) if $data_charset ;
	    $content= base64($content) ;
	    return $data_charset  ? "data:$type;charset=$data_charset;base64,$content"
				  : "data:$type;base64,$content" ;
	} else {
	    return $uri_ref ;
	}
    }

    # Separate fragment from URI
    my($uri, $frag)= $uri_ref=~ /^([^#]*)(#.*)?/ ;
    return $uri_ref if $uri eq '' ;  # allow bare fragments to pass unchanged

    # Hack here-- some sites (e.g. eBay) create erroneous URLs with linefeeds
    #   in them, which makes the links unusable if they are encoded here.
    #   So, here we strip CR and LF from $uri before proceeding.  :P
    $uri=~ s/[\015\012]//g ;

    # Sometimes needed for SWF apps; see comments above this routine.
    my($query) ;
    ($uri, $query)= split(/\?/, $uri)  if $retain_query ;
    $query= '?' . $query   if $query ;

    # calculate absolute URL based on five possible cases
    my($absurl)=
	    $uri=~ m#^[\w+.-]*:#i   ?  $uri                 # absolute URL
	  : $uri=~ m#^//#           ?  $base_scheme . $uri  # net_path (rare)
	  : $uri=~ m#^/#            ?  $base_host . $uri    # abs_path, rel URL
	  : $uri=~ m#^\?#           ?  $base_file . $uri    # abs_path, rel URL
	  :                            $base_path . $uri ;  # relative path

    return $url_start . &wrap_proxy_encode($absurl) . $query . $frag ;
}


# Identical to full_url(), except second parameter explicitly determines
#   whether we use $url_start_inframe or $url_start_noframe.
# This could be wrapped into the full_url() routine, but I'm guessing it
#   is more efficient to do it this way.  This won't be called often and
#   full_url() is called a lot.
# This uses a little trick with local() that lets us use full_url(), which
#   keeps the routines synchronized and reduces code size.  We set a local
#   version of $url_start, which is used by full_url() because it remains
#   in scope there, but when we exit this routine the scope closes and
#   the old $url_start is restored.
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_full_url_by_frame() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of this routine.
sub full_url_by_frame {
    my($uri_ref, $is_frame)= @_ ;
    local($url_start)= $is_frame   ? $url_start_inframe  : $url_start_noframe ;
    return &full_url($uri_ref) ;
}



# Set globals $base_url, $base_scheme, $base_host, $base_path, and $base_file,
#   based on value of $base_url.  This must be called whenever $base_url is
#   set, which unfortunately may vary over the course of the program.
# These are an integral part of &full_url(), placed outside of that for speed.
# To specify:
#   $base_scheme is the scheme of the base URL, ending in ":", like "http:".
#   $base_host is the scheme/host/port of the base URL, with no final slash.
#   $base_path is the scheme/host/port/path, through final slash.
#   $base_file is the scheme/host/port/path, *including* file, but not query.
# These are only relevant (and accurate) for hierarchical "/"-using schemes,
#   like HTTP or FTP.
# Any HTML-escaping/unescaping should be done outside of this routine.
sub fix_base_vars {
    $base_url=~ s/\A\s+|\s+\Z//g ;  # remove leading/trailing spaces

    # Guarantee that $base_url has at least a path of '/', inserting before
    #   ?query if needed.
    $base_url=~ s#^([\w+.-]+://[^/?]+)/?#$1/# ;

    ($base_scheme)= $base_url=~ m#^([\w+.-]+:)//# ;
    ($base_host)=   $base_url=~ m#^([\w+.-]+://[^/?]+)# ; # no ending slash
    ($base_path)=   $base_url=~ m#^([^?]*/)# ;            # use greedy matching
    ($base_file)=   $base_url=~ m#^([^?]*)# ;
}


# Because encoding and decoding the URL requires some steps that are not
#   user-configurable, we "purify" the functions proxy_encode() and
#   proxy_decode() and move the extra steps to these wrapper functions.
# Don't encode the URI fragment.
# Don't decode the query component or URI fragment.
# Note that we encode "?" to "=3f", and similar for "=" itself.  This is to
#   prevent "?" from being in the encoded URL, where it would prematurely
#   terminate PATH_INFO.
# Also, Apache has a bug where it compresses multiple "/" in PATH_INFO.  To
#   work around this, we encode all "//" to "/=2f", which will be unencoded
#   by proxy_decode() as described in the previous paragraph.  Same goes for
#   "%", since Apache has the same problem when "%2f%2f" is in PATH_INFO.
sub wrap_proxy_encode {
    my($URL)= @_ ;

    my($uri, $frag)= $URL=~ /^([^#]*)(.*)/ ;

    $uri= &proxy_encode($uri) ;

    # Encode ? so it doesn't prematurely end PATH_INFO.
    $uri=~ s/=/=3d/g ;
    $uri=~ s/\?/=3f/g ;
    $uri=~ s/%/=25/g ;
    $uri=~ s/&/=26/g ;
    $uri=~ s/;/=3b/g ;
    1 while $uri=~ s#//#/=2f#g ;    # work around Apache PATH_INFO bug

    return $uri . $frag ;
}


sub wrap_proxy_decode {
    my($enc_URL)= @_ ;

    my($uri, $query, $frag)= $enc_URL=~ /^([^?#]*)([^#]*)(.*)/ ;

    # First, un-encode =xx chars.
    $uri=~ s/=([0-9A-Fa-f]{2})/chr(hex($1))/ge ;

    $uri= &proxy_decode($uri) ;

    return $uri . $query . $frag ;
}



# Given a block of code, convert it to be "proxy-safe", depending on
#   the given content type (language).  Usually that conversion just means
#   updating any URLs in it.
# This is used for style sheets, scripts, etc.
# Preserve correct quotes.
# Returns a two-element array of the proxified string, and any remainder that
#   couldn't be proxified.  This is needed to support erroneous "</script>"
#   strings within literal strings in JavaScript blocks.  :P
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_proxify_block() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of this routine.
# ALSO: Depending what you change here, the routine _proxy_jslib_proxify_css()
#   may be affected.
sub proxify_block {
    my($s, $type)= @_ ;

    if ($scripts_are_banned_here) {
	return undef if $type=~ /^$SCRIPT_TYPE_REGEX$/io ;
    }

    if ($type eq 'text/css') {
	# The only URIs in CSS2 are invoked with "url(...)" or "@import".
	#   (Are there any more?)
	# Ugly regex, but gets virtually all real matches and is privacy-safe.
	# Hard part is handling "\"-escaping.  See
	#   http://www.w3.org/TR/REC-CSS2/syndata.html#uri
	# Hopefully we'll use a whole different approach in the new rewrite.

	$s=~ s/\burl\s*\(\s*(([^)]*\\\))*[^)]*)(\)|$)/
	      'url(' . &css_full_url($1) . ')'     /gie ;

	$s=~ s#\@import\s*("[^"]*"|'[^']*'|(?!url\s*\()[^;\s<]*)#
	       '@import ' . &css_full_url($1)                   #gie ;

	# Proxify any strings inside "expression()" or "function()".
	$s= &proxify_expressions_in_css($s)
	    if $s=~ /\b(?:expression|function)\s*\(/i ;

	return ($s, '') ;


    # JavaScript can be identified by any of these MIME types.  :P  The
    #   "ecma" ones are the standard, the "javascript" and "livescript" ones
    #   refer to Netscape's implementations, and the "jscript" one refers to
    #   Microsoft's implementation.  Until we need to differentiate, let's
    #   treat them all the same here.
    } elsif ($type=~ m#^(application/x-javascript|application/x-ecmascript|application/javascript|application/ecmascript|text/javascript|text/ecmascript|text/livescript|text/jscript)$#i) {

	# Slight hack-- verify $PROXIFY_SCRIPTS is true, since this may be
	#   called even when it's not true (e.g. style sheets of script type).
	return ($s, '') unless $PROXIFY_SCRIPTS ;

	return &proxify_js($s, 1) ;   # ... which returns two values


    # Handle ShockWave Flash resources.
    } elsif ($type eq 'application/x-shockwave-flash') {

	return (&proxify_swf($s), '') if $PROXIFY_SWF ;

	# Remove if not $ALLOW_UNPROXIFIED_SCRIPTS .
	return ($s, '') if $ALLOW_UNPROXIFIED_SCRIPTS ;

	return ('', '') ;


    # For any non-supported script type, either remove it or pass it unchanged.
    } elsif ($type=~ /^$SCRIPT_TYPE_REGEX$/io) {
	return $ALLOW_UNPROXIFIED_SCRIPTS  ? ($s, '')  : ('', '') ;


    } else {
	# If we don't understand the type, return the block unchanged.
	# This would be a privacy hole, if we didn't check for script types
	#   when $scripts_are_banned_here above.  If later we want the option
	#   of returning undef for an unknown type, we can add a parameter to
	#   specify that.

	return ($s, '') ;

    }

}



# For CSS only:  takes entire contents between parentheses in "url(...)",
#   extracts the URL therein (accounting for quotes, "\"-escaped chars, etc.),
#   and returns the full_url() of that, suitable for placing back inside
#   "url(...)", including all "\"-escaping, quotes, etc.  :P
# Preserve correct quotes, because this may be embedded in a larger quoted
#   context.
# In external style sheets, relative URLs are resolved relative to the style
#   sheet, not the source HTML document.  This makes it easy for us-- no
#   special $base_url handling.
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_css_full_url() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   (almost) a Perl-to-JavaScript translation of this routine.
sub css_full_url {
    my($url)= @_ ;
    my($q) ;

    $url=~ s/\s+$// ;       # leading spaces already stripped above
    if    ($url=~ /^"/)  { $q= '"' ; $url=~ s/^"|"$//g }  # strip quotes
    elsif ($url=~ /^'/)  { $q= "'" ; $url=~ s/^'|'$//g }
    $url=~ s/\\(.)/$1/g ;   # "\"-unescape
    $url=~ s/^\s+|\s+$//g ; # finally, strip spaces once more

    $url= &full_url($url) ;

    $url=~ s/([(),\s'"\\])/\\$1/g ;    # put "\"-escaping back in

    return $q . $url . $q ;
}


# Some CSS (MSIE-only?) may use the "expression" or "function" constructs,
#   whose contents inside "()" are to be interpreted and executed as
#   JavaScript.  We have to handle nested parentheses, so we utilize the
#   already-existing get_next_js_expr() to read the JS code inside the "()".
# jsm-- this may need to be done in JS too.
sub proxify_expressions_in_css {
    my($s)= @_ ;
    my(@out) ;

    while ($s=~ /(\G.*?(?:expression|function)\s*\()/gcis) {
	push(@out, $1) ;
	push(@out, (&proxify_js(&get_next_js_expr(\$s, 1)))[0]) ;
	return undef unless $s=~ /\G\)/gc ;
	push(@out, ')') ;
    }
    return join('', @out, substr($s, pos($s))) ;
}


# This is a hack for supporting Flash apps that use Adobe's shared/cached .swz
#   libraries, which are downloaded from Adobe's site but which we don't know
#   how to parse yet.  So proxify any fields in the flashvars string that might
#   be URLs.  To start with, "src" and "poster" are used by Adobe's Strobe.
# jsm-- must do this in JS too....
sub proxify_flashvars {
    my($fv)= @_ ;
    return $fv unless $fv ne '' ;
    my %fv= getformvars($fv) ;
    my $rebuild ;

    $fv{src}=    full_url($fv{src}), $rebuild= 1     if defined $fv{src} ;
    $fv{poster}= full_url($fv{poster}), $rebuild= 1  if defined $fv{poster} ;

    return $fv unless $rebuild ;

    my($name, $value, @ret) ;
    while (($name, $value)= each %fv) {
	$name=~  s/(\W)/ '%' . sprintf('%02x',ord($1)) /ge ;
	$value=~ s/(\W)/ '%' . sprintf('%02x',ord($1)) /ge ;
	push(@ret, "$name=$value") ;
    }
    return join('&', @ret) ;   # should use ";" but not all apps read that correctly
}



#--------------------------------------------------------------------------
#    Scheme-specific routines
#--------------------------------------------------------------------------

#
# <scheme>_get: get resource at URL and set globals $status, $headers, $body,
#   and $is_html.  Optionally, set $response_sent to signal that the response
#   has already been sent.  These are all globals for speed, to prevent
#   unneeded copying of huge strings.
#

# http_get: actually supports both GET and POST.  Also, it is used for
#   https:// (SSL) URLs in addition to normal http:// URLs.

sub http_get {
    my($default_port, $portst, $realhost, $realport, $request_uri,
       $realm, $tried_realm, $auth,
       $proxy_auth_header, $accept_language_header, $content_type,
       $lefttoget, $postblock, @postbody, $body_too_big, $rin,
       $status_code, $footers) ;
    local($/)= "\012" ;

    # Localize filehandles-- safer for when using mod_perl, early exits, etc.
    # But unfortunately, it doesn't work well with tied variables.  :(
    local(*S, *S_PLAIN) ;

    # If using SSL, then verify that we're set up for it.
    if ($scheme eq 'https') {
	eval { require Net::SSLeay } ;  # don't check during compilation
	&no_SSL_warning($URL) if $@ ;

	# Fail if we're being asked to use SSL, and we're not on an SSL server.
	# Do NOT remove this code; instead, see note above where
	#   $OVERRIDE_SECURITY is set.
	&insecure_die  if !$RUNNING_ON_SSL_SERVER && !$OVERRIDE_SECURITY ;
    }


    $default_port= $scheme eq 'https'  ? 443  : 80 ;

    $port= $default_port if $port eq '' ;

    # Some servers don't like default port in a Host: header, so use $portst.
    $portst= ($port==$default_port)  ? ''  : ":$port" ;

    $realhost= $host ;
    $realport= $port ;
    $request_uri= $path ;
    $request_uri=~ s/ /%20/g ;    # URL-encode spaces for now; maybe more in the future

    # there must be a smoother way to handle proxies....
    if ($scheme eq 'http' && $HTTP_PROXY) {
	my($dont_proxy) ;
	foreach (@NO_PROXY) {
	    $dont_proxy= 1, last if $host=~ /\Q$_\E$/i ;
	}
	unless ($dont_proxy) {
	    ($realhost, $realport)=
		$HTTP_PROXY=~ m#^(?:http://)?([^/?:]*):?([^/?]*)#i ;
	    $realport= 80 if $realport eq '' ;
	    $request_uri= "$scheme://$authority$request_uri" ;  # rebuild to include encoded path
	    $proxy_auth_header= "Proxy-Authorization: Basic $PROXY_AUTH\015\012"
	       if $PROXY_AUTH ne '' ;
	}
    }

    # Apparently, some servers don't handle a blank Accept-Language: header,
    #   so only include it in the request if it's not blank.
    $accept_language_header= "Accept-Language: $ENV{HTTP_ACCEPT_LANGUAGE}\015\012"
	if $ENV{HTTP_ACCEPT_LANGUAGE} ne '' ;


    #------ Connect socket to host; send request; wait with select() ------

    # To be able to retry on a 401 Unauthorized response, put the whole thing
    #   in a labeled block.  Note that vars have to be reinitialized.
    HTTP_GET: {

	# Open socket(s) as needed, taking into account possible SSL, proxy, etc.
	# Whatever the situation, S will be the socket to handle the plaintext
	#   HTTP exchange (which may be encrypted by a lower level).

	# If using SSL, then open a plain socket S_PLAIN to the server and
	#   create an SSL socket handle S tied to the plain socket, such that
	#   whatever we write to S will be written encrypted to S_PLAIN (and
	#   similar for reads).  If using an SSL proxy, then connect to that
	#   instead and establish an encrypted tunnel to the destination server
	#   using the CONNECT method.
	if ($scheme eq 'https') {
	    my($dont_proxy) ;
	    if ($SSL_PROXY) {
		foreach (@NO_PROXY) {
		    $dont_proxy= 1, last if $host=~ /$_$/i ;
		}
	    }

	    # If using an SSL proxy, then connect to it and use the CONNECT
	    #   method to establish an encrypted tunnel.  The CONNECT method
	    #   is an HTTP extension, documented in RFC 2817.
	    # This block is modelled after code sent in by Grant DeGraw.
	    if ($SSL_PROXY && !$dont_proxy) {
		($realhost, $realport)=
		    $SSL_PROXY=~ m#^(?:http://)?([^/?:]*):?([^/?]*)#i ;
		$realport= 80 if $realport eq '' ;
		&newsocketto('S_PLAIN', $realhost, $realport) ;

		# Send CONNECT request.
		print S_PLAIN "CONNECT $host:$port HTTP/$HTTP_VERSION\015\012",
			      'Host: ', $host, $portst, "\015\012" ;
		print S_PLAIN "Proxy-Authorization: Basic $SSL_PROXY_AUTH\015\012"
		    if $SSL_PROXY_AUTH ne '' ;
		print S_PLAIN "\015\012" ;

		# Wait a minute for the response to start
		vec($rin= '', fileno(S_PLAIN), 1)= 1 ;
		select($rin, undef, undef, 60)
		    || &HTMLdie("No response from SSL proxy") ;

		# Read response to CONNECT.  All we care about is the status
		#   code, but we have to read the whole response.
		my($response, $status_code) ;
		do {
		    $response= '' ;
		    do {
			$response.= $_= <S_PLAIN> ;
		    } until (/^(\015\012|\012)$/) ; #lines end w/ LF or CRLF
		    ($status_code)= $response=~ m#^HTTP/\d+\.\d+\s+(\d+)# ;
		} until $status_code ne '100' ;

		# Any 200-level response is OK; fail otherwise.
		&HTMLdie("SSL proxy error; response was:<p><pre>$response</pre>")
		    unless $status_code=~ /^2/ ;

	    # If not using a proxy, then open a socket directly to the server.
	    } else {
		&newsocketto('S_PLAIN', $realhost, $realport) ;
	    }

	    # Either way, make an SSL socket S tied to the plain socket S_PLAIN.
	    my $ssl_obj= tie(*S, 'SSL_Handle', \*S_PLAIN) ;
	    Net::SSLeay::connect($ssl_obj->{SSL}) or &HTMLdie("Can't SSL connect: $!") ;


	# If not using SSL, then just open a normal socket.  Any proxy is
	#   already set in $realhost and $realport, above.
	} else {
	    &newsocketto('S', $realhost, $realport) ;
	}


	binmode S ;   # see note with "binmode STDOUT", above


	# Send the request.
	# The Host: header is required in HTTP 1.1 requests.  Also include
	#   Accept: and User-Agent: because they affect results.
	# We're anonymously browsing, so don't include the From: header.  The
	#   User-Agent: header is a very teensy privacy risk, but some pages
	#   load differently with different browsers.  Referer: is handled
	#   below, depending on the user option.
	# Ultimately, we may want to check ALL possible request headers-- see
	#   if they're provided in $ENV{HTTP_xxx}, and include them in our
	#   request if appropriate as per the HTTP spec regarding proxies, and
	#   if they don't violate our goals here (e.g. privacy); some may need
	#   to be appropriately modified to pass through this proxy.  Each
	#   request header would have to be considered and handled individually.
	#   That's probably not all necessary, but we can take that approach as
	#   priorities dictate.
	# Note that servers are NOT required to provide request header values
	#   to CGI scripts!  Some do, but it must not be relied on.  Apache does
	#   provide them, and even provides unknown headers-- e.g. a "Foo: bar"
	#   request header will literally set HTTP_FOO to "bar".  (But some
	#   headers are explicitly discouraged from being given to CGI scripts,
	#   such as Authorization:, because that would be a security hole.)

	print S $ENV{'REQUEST_METHOD'}, ' ', $request_uri, " HTTP/$HTTP_VERSION\015\012",
		'Host: ', $host, $portst, "\015\012",    # needed for multi-homed servers
		'Accept: ', $env_accept, "\015\012",     # possibly modified
		'User-Agent: ', $USER_AGENT || $ENV{'HTTP_USER_AGENT'}, "\015\012",
		$accept_language_header,
		$proxy_auth_header ;                     # empty if not needed


	# Handle potential gzip encoding and the Accept-Encoding: header.
	# Currently, we only handle the gzip encoding, not compress or deflate.
	# A blank Accept-Encoding: header indicates that we don't support any
	#   encoding (like gzip).  Unfortunately, though, at least one server
	#   (Boa) chokes on an empty Accept-Encoding: header, so let's make it
	#   a "," here.  That effectively still means an empty value, according
	#   to the rules of HTTP header values.
	if ($ENV{HTTP_ACCEPT_ENCODING}=~ /\bgzip\b/i) {
	    eval { require IO::Uncompress::Gunzip } ;  # don't check during compilation
	    print S ($@  ? "Accept-Encoding: ,\015\012"
			 : "Accept-Encoding: gzip\015\012") ;
	} else {
	    print S "Accept-Encoding: ,\015\012" ;
	}


	# Create Referer: header if so configured.
	# Only include Referer: if we successfully remove $script_url+flags from
	#   start of referring URL.  Note that flags may not always be there.
	# If using @PROXY_GROUP, loop through them until one fits.  This could
	#   only be ambiguous if one proxy in @PROXY_GROUP is called through
	#   another proxy in @PROXY_GROUP, which you really shouldn't do anyway.
	# Do not send Referer: beginning with "https" unless the requested
	#   URL also begins with "https"!  Security hole otherwise.
	if (!$e_hide_referer) {
	    my($referer)= $ENV{'HTTP_REFERER'} ;
	    if (@PROXY_GROUP) {
		foreach (@PROXY_GROUP) {
		    if ($referer=~ s#^$_(/[^/]*/?)?##  &&  $referer ne '') {
			my $decoded_referer= &wrap_proxy_decode($referer) ;
			print S 'Referer: ', $decoded_referer, "\015\012"
			    unless $decoded_referer=~ /^https\b/i && $scheme eq 'http';
			last ;
		    }
		    last if $referer eq '' ;
		}
	    } else {
		if ($referer=~ s#^$THIS_SCRIPT_URL(/[^/]*/?)?##  &&  ($referer ne '')) {
		    my $decoded_referer= &wrap_proxy_decode($referer) ;
		    print S 'Referer: ', $decoded_referer, "\015\012"
			unless $decoded_referer=~ /^https\b/i && $scheme eq 'http';
		}
	    }
	}


	# Add "Connection: close" header if we're using HTTP 1.1 and aren't running as a daemon.
	print S "Connection: close\015\012"
	    if $HTTP_VERSION eq '1.1' and ($RUN_METHOD eq 'mod_perl' or $RUN_METHOD eq 'cgi') ;

	# Add the cookie if it exists and cookies aren't banned here.
	print S 'Cookie: ', $cookie_to_server, "\015\012"
	    if !$cookies_are_banned_here && ($cookie_to_server ne '') ;

	# Add Pragma: and Cache-Control: headers if they were given in the
	#   request, to allow caches to behave properly.  These two headers
	#   need no modification.
	# As explained above, we can't rely on request headers being provided
	#   to the script via environment variables.
	print S "Pragma: $ENV{HTTP_PRAGMA}\015\012" if $ENV{HTTP_PRAGMA} ne '' ;
	print S "Cache-Control: $ENV{HTTP_CACHE_CONTROL}\015\012"
	    if $ENV{HTTP_CACHE_CONTROL} ne '' ;


	# Add Authorization: header if we've had a challenge.
	if ($realm ne '') {
	    # If we get here, we know $realm has a defined $auth and has not
	    #   been tried.
	    print S 'Authorization: Basic ', $auth{$realm}, "\015\012" ;
	    $tried_realm= $realm ;

	} else {
	    # If we have auth information for this server, what the hey, let's
	    #   try one, it may save us a request/response cycle.
	    # First case is for rare case when auth info is in URL.  Related
	    #   block 100 lines down needs no changes.
	    if ($username ne '') {
		print S 'Authorization: Basic ',
			&base64($username . ':' . $password),
			"\015\012" ;
	    } elsif ( ($tried_realm,$auth)= each %auth ) {
		print S 'Authorization: Basic ', $auth, "\015\012" ;
	    }
	}


	# Some old XMLHTTPRequest server apps require this non-standard header.
	# Thanks to Devesh Parekh for the patch.
	print S "X-Requested-With: $ENV{HTTP_X_REQUESTED_WITH}\015\012"
	    if $expected_type eq 'x-proxy/xhr' and $ENV{HTTP_X_REQUESTED_WITH} eq 'XMLHttpRequest' ;

	# Another non-standard HTTP request header.
	print S "X-Do-Not-Track: 1\015\012"  if $ENV{HTTP_X_DO_NOT_TRACK} eq '1' ;

	# Another non-standard HTTP request header.
	print S "DNT: 1\015\012"  if $ENV{HTTP_DNT} eq '1' ;



	# A little problem with authorization and POST requests: If auth
	#   is required, we won't know which realm until after we make the
	#   request and get part of the response.  But to make the request,
	#   we have to send the entire POST body, because some servers
	#   mistakenly require that before returning even an error response.
	#   So this means we have to send the entire POST body, and be
	#   prepared to send it a second time, thus we have to store it
	#   locally.  Either that, or fail to send the POST body a second
	#   time.  Here, we let the owner of this proxy set $MAX_REQUEST_SIZE:
	#   store and post a second time if a request is smaller, or else
	#   die with 413 the second time through.

	# If request method is POST, copy content headers and body to request.
	# The first time through here, save body to @postbody, if the body's
	#   not too big.
	if ($ENV{'REQUEST_METHOD'} eq 'POST') {

	    if ($body_too_big) {
		# Quick 'n' dirty response for an unlikely occurrence.
		# 413 is not actually an HTTP/1.0 response...
		&HTMLdie("Sorry, this proxy can't handle a request larger "
		       . "than $MAX_REQUEST_SIZE bytes at a password-protected"
		       . " URL.  Try reducing your submission size, or submit "
		       . "it to an unprotected URL.", 'Submission too large',
			 '413 Request Entity Too Large') ;
	    }

	    # Otherwise...
	    $lefttoget= $ENV{'CONTENT_LENGTH'} ;
	    print S 'Content-type: ', $ENV{'CONTENT_TYPE'}, "\015\012",
		    'Content-length: ', $lefttoget, "\015\012\015\012" ;

	    if (@postbody) {
		print S @postbody ;
	    } else {
		$body_too_big= ($lefttoget > $MAX_REQUEST_SIZE) ;

		# Loop to guarantee all is read from $STDIN.
		do {
		    $lefttoget-= read($STDIN, $postblock, $lefttoget) ;
		    print S $postblock ;
		    # efficient-- only doing test when input is slow anyway.
		    push(@postbody, $postblock) unless $body_too_big ;
		} while $lefttoget && ($postblock ne '') ;
	    }

	# For GET or HEAD requests, just add extra blank line.
	} else {
	    print S "\015\012" ;
	}


	# Wait a minute for the response to start
	vec($rin= '', fileno(S), 1)= 1 ;
	select($rin, undef, undef, 60)
	    || &HTMLdie("No response from $realhost:$realport") ;


	#------ Read full response into $status, $headers, and $body ----

	# Support both HTTP 1.x and HTTP 0.9
	$status= <S> ;  # first line, which is the status line in HTTP 1.x


	# HTTP 0.9
	# Ignore possibility of HEAD, since it's not defined in HTTP 0.9.
	# Do any HTTP 0.9 servers really exist anymore?
	unless ($status=~ m#^HTTP/#) {
	    $is_html= 1 ;   # HTTP 0.9 by definition implies an HTML response
	    $content_type= 'text/html' ;
	    local($/)= undef ;
	    $body= $status . <S> ;
	    $status= '' ;

	    close(S) ;
	    untie(*S) if $scheme eq 'https' ;
	    return ;
	}


	# After here, we know we're using HTTP 1.x

	# Be sure to handle case when server doesn't send blank line!  It's
	#   rare and erroneous, but a couple servers out there do that when
	#   responding with a redirection.  This can cause some processes to
	#   linger and soak up resources, particularly under mod_perl.
	# To handle this, merely check for eof(S) in until clause below.
	# ... except that for some reason invoking eof() on a tied SSL_Handle
	#   makes later read()'s fail with unlikely error messages.  :(
	#   So instead of eof(S), test "$_ eq ''".

	# Loop to get $status and $headers until we get a non-100 response.
	do {
	    ($status_code)= $status=~ m#^HTTP/\d+\.\d+\s+(\d+)# ;

	    $headers= '' ;   # could have been set by first attempt
	    do {
		$headers.= $_= <S> ;    # $headers includes last blank line
#	    } until (/^(\015\012|\012)$/) || eof(S) ; # lines end w/ LF or CRLF
	    } until (/^(\015\012|\012)$/) || $_ eq '' ; #lines end w/ LF or CRLF

	    $status= <S> if $status_code == 100 ;  # re-read for next iteration
	} until $status_code != 100 ;

	# Unfold long header lines, a la RFC 822 section 3.1.1
	$headers=~ s/(\015\012|\012)[ \t]+/ /g ;


	# Check for 401 Unauthorized response
	if ($status=~ m#^HTTP/\d+\.\d+\s+401\b#) {
	    ($realm)=
		$headers=~ /^WWW-Authenticate:\s*Basic\s+realm="([^"\n]*)/mi ;
	    &HTMLdie("Error by target server: no WWW-Authenticate header.")
		unless $realm ne '' ;

	    if ($auth{$realm} eq '') {
		&get_auth_from_user("$host$portst", $realm, $URL) ;
	    } elsif ($realm eq $tried_realm) {
		&get_auth_from_user("$host$portst", $realm, $URL, 1) ;
	    }

	    # so now $realm exists, has defined $auth, and has not been tried
	    close(S) ;
	    untie(*S) if $scheme eq 'https' ;
	    redo HTTP_GET ;
	}


	# Extract $content_type, used in several places
	($content_type, $charset)=
	    $headers=~ m#^Content-Type:\s*([\w/.+\$-]*)\s*;?\s*(?:charset\s*=\s*([\w-]+))?#mi ;
	$content_type= lc($content_type) ;


	# If we're text only, then cut off non-text responses (but allow
	#   unspecified types).
	if ($TEXT_ONLY) {
	    if ( ($content_type ne '') && ($content_type!~ m#^text/#i) ) {
		&non_text_die ;
	    }
	}

	# If we're removing scripts, then disallow script MIME types.
	if ($scripts_are_banned_here) {
	    &script_content_die  if $content_type=~ /^$SCRIPT_TYPE_REGEX$/io ;

	    # Note that the non-standard Link: header, which may link to a
	    #   style sheet, is handled in http_fix().
	}


	# If URL matches one of @BANNED_IMAGE_URL_PATTERNS, then skip the
	#   resource unless it's clearly a text type.
	if ($images_are_banned_here) {
	    &skip_image  unless $content_type=~ m#^text/#i ;
	}

	# Keeping $base_url and its related variables up-to-date is an
	#   ongoing job.  Here, we look in appropriate headers.  Note that if
	#   Content-Base: doesn't exist, Content-Location: is an absolute URL.
	if        ($headers=~ m#^Content-Base:\s*([\w+.-]+://\S+)#mi) {
	    $base_url= $1, &fix_base_vars ;
	} elsif   ($headers=~ m#^Content-Location:\s*([\w+.-]+://\S+)#mi) {
	    $base_url= $1, &fix_base_vars ;
	} elsif   ($headers=~ m#^Location:\s*([\w+.-]+://\S+)#mi) {
	    $base_url= $1, &fix_base_vars ;
	}

	# Now, fix the headers with &http_fix().  It uses &full_url(), and
	#   may modify the headers we just extracted the base URL from.
	# This also includes cookie support.
	&http_fix ;



	# If configured, make this response as non-cacheable as possible.
	#   This means remove any Expires: and Pragma: headers (the latter
	#   could be using extensions), strip Cache-Control: headers of any
	#   unwanted directives and add the "no-cache" directive, and add back
	#   to $headers the new Cache-Control: header and a "Pragma: no-cache"
	#   header.
	# A lot of this is documented in the HTTP 1.1 spec, sections 13 as a
	#   whole, 13.1.3, 13.4, 14.9, 14.21, and 14.32.  The Cache-Control:
	#   response header has eight possible directives, plus extensions;
	#   according to section 13.4, all except "no-cache", "no-store", and
	#   "no-transform" might indicate cacheability, so remove them.  Remove
	#   extensions for the same reason.  Remove any parameter from
	#   "no-cache", because that would limit its effect.  This effectively
	#   means preserve only "no-store" and "no-transform" if they exist
	#   (neither have parameters), and add "no-cache".
	# We use a quick method here that works for all but cases both faulty
	#   and obscure, but opens no privacy holes; in the future we may fully
	#   parse the header value(s) into its comma-separated list of
	#   directives.

	if ($MINIMIZE_CACHING) {
	    my($new_value)= 'no-cache' ;
	    $new_value.= ', no-store'
		if $headers=~ /^Cache-Control:.*?\bno-store\b/mi ;
	    $new_value.= ', no-transform'
	      if $headers=~ /^Cache-Control:.*?\bno-transform\b/mi ;

	    my($no_cache_headers)=
		"Cache-Control: $new_value\015\012Pragma: no-cache\015\012" ;

	    $headers=~ s/^Cache-Control:[^\012]*\012?//mig ;
	    $headers=~ s/^Pragma:[^\012]*\012?//mig ;
	    $headers=~ s/^Expires:[^\012]*\012?//mig ;

	    $headers= $no_cache_headers . $headers ;
	}


	# Add the 1-2 session cookies if so configured.
	$headers= $session_cookies . $headers  if $session_cookies ;


	# Set $is_html if headers indicate HTML response.
	# Question: are there any other HTML-like MIME types, including x-... ?
	$is_html= 1  if   $content_type eq 'text/html'
		       or $content_type eq 'application/xhtml+xml' ;


	# Some servers return HTML content without the Content-Type: header.
	#   These MUST be caught, because Netscape displays them as HTML, and
	#   a user could lose their anonymity on these pages.
	# According to the HTTP 1.1 spec, section. 7.2.1, browsers can choose
	#   how to deal with HTTP bodies with no Content-Type: header.  See
	#       http://www.ietf.org/rfc/rfc2616.txt
	# In such a case, Netscape seems to always assume "text/html".
	#   Konqueror seems to guess the MIME type by using the Unix "file"
	#   utility on the first 1024 bytes, and possibly other clues (e.g.
	#   resource starts with "<h1>").
	# In any case, we must interpret as HTML anything that *may* be
	#   interpreted as HTML by the browser.  So if there is no
	#   Content-Type: header, set $is_html=1 .  The worst that would
	#   happen would be the occasional content mangled by modified URLs,
	#   which is better than a privacy hole.

	$is_html= 1  if ($content_type eq '') ;

	# If the expected type is "x-proxy/xhr", then the resource is being
	#   downloaded via a JS XMLHttpRequest object and should not be
	#   proxified, even if it's HTML data (it would be proxified later
	#   when the data is written to or inserted in a document).  To
	#   indicate this, we set $is_html to false.
	$is_html= 0  if ($expected_type eq 'x-proxy/xhr') ;

	# To support non-NPH hack, replace first part of $status with
	#   "Status:" if needed.
	$status=~ s#^\S+#Status:#  if $NOT_RUNNING_AS_NPH ;

	# A bug in some Sun servers returns "text/plain" for SWF files when
	#   responding to certain SWF method calls.
	my $may_be_swf= ($content_type eq 'text/plain'
			 and $headers=~ /^Server:\s*Sun-ONE/mi) ;


	# To support streaming media and large files, read the data from
	#   the server and send it immediately to the client.  The exception
	#   is HTML content, which still must be read fully to be converted
	#   in the main block.  HTML content is not normally streaming or
	#   very large.
	# This requires $status and $headers to be returned now, which is
	#   OK since headers have been completely cleaned up by now.  This
	#   also means that changes after this point to $body won't
	#   have any effect, which in fact is fine in the case of non-HTML
	#   resources.  Set $response_sent to prevent the main block from
	#   sending a response.
	# Also, handle any non-HTML types here which must be proxified.
	# This is a bit sloppy now, just a quick hack to get rudimentary
	#   handling of multiple types working and released.  It will be
	#   rewritten more cleanly at some point, when the whole proxifying
	#   of different types is modularized better.

	# Only read body if the request method is not HEAD
	if ($ENV{'REQUEST_METHOD'} ne 'HEAD') {

	    # Because of the erroneous way some browsers use the expected
	    #   MIME type instead of the actual Content-Type: header, check
	    #   $expected_type first.
	    # Since style sheets tend to be automatically loaded, whereas other
	    #   types (like scripts) are more user-selected, plus the fact that
	    #   CSS can be safely proxified and scripts cannot, we treat a
	    #   resource as CSS if it *may* be treated as CSS by the browser.
	    #   This is relevant when $expected_type and Content-Type: differ.
	    # Again, anything retrieved via a JS XMLHttpRequest object should
	    #   not be proxified, regardless of $content_type .

	    if ( ($expected_type ne 'x-proxy/xhr') &&
		 (   ($expected_type=~ /^$TYPES_TO_HANDLE_REGEX$/io)
		  || ($content_type=~  /^$TYPES_TO_HANDLE_REGEX$/io)
		  || $may_be_swf )  )
	    {
		my($type) ;
		if ( ($expected_type eq 'text/css') || ($content_type eq 'text/css') ) {
		    $type= 'text/css' ;
		} elsif ($expected_type=~ /^$TYPES_TO_HANDLE_REGEX$/io) {
		    $type= $expected_type ;
		} else {
		    $type= $content_type ;
		}

		# If response is chunked, then dechunk it before processing.
		# Not perfect (it loses the benefit of chunked encoding), but it
		#   works and will seldom be a problem.
		# Append $footers into $headers, and remove any Transfer-Encoding: header.
		if ($headers=~ /^Transfer-Encoding:[ \t]*chunked\b/mi) {
		    ($body, $footers)= &get_chunked_body('S') ;
		    &HTMLdie(&HTMLescape("Error reading chunked response from $URL ."))
			unless defined($body) ;
		    $headers=~ s/^Transfer-Encoding:[^\012]*\012?//mig ;
		    $headers=~ s/^(\015\012|\012)/$footers$1/m ;

		# Handle explicitly sized response.
		} elsif ($headers=~ /^Content-Length:[ \t]*(\d+)/mi) {
		    $body= &read_socket('S', $1) ;

		# If not chunked or sized, read entire input into $body.
		} else {
		    local($/)= undef ;
		    $body= <S> ;
		}

		shutdown(S, 0)  if $RUNNING_ON_IIS ;  # without this, IIS+MSIE hangs

		# If $body is gzipped, then gunzip it.
		# Change $headers to maintain consistency, even though it will
		#   probably just be compressed again later.
		if ($headers=~ /^Content-Encoding:.*\bgzip\b/mi) {
		    eval { require IO::Uncompress::Gunzip } ;
		    &no_gzip_die if $@ ;
		    my $zout ;
		    IO::Uncompress::Gunzip::gunzip(\$body => \$zout)
			or HTMLdie("Couldn't gunzip: $IO::Uncompress::Gunzip::GunzipError") ;
		    $body= $zout ;
		    $headers=~ s/^Content-Encoding:.*?\012//gims ;
		}

		# A body starting with "\xEF\xBB\xBF" (non-standardly) indicates
		#   a UTF-8 resource.  We can only know this after reading
		#   $body, thus it's done here and not above.
		# The string "\xEF\xBB\xBF" is sort of like a non-standard BOM 
		#   for UTF-8, though UTF-8 doesn't need a BOM.  Some systems
		#   don't handle it, so remove it if found.
		$charset= 'UTF-8' if $body=~ s/^\xef\xbb\xbf// ;

		# Decode $body if $charset is defined.
		if (defined $charset) {
		    eval { $body= decode($charset, $body) } ;
		    &malformed_unicode_die($charset) if $@ ;
		}

		# If $body looks like it's in UTF-16 encoding, then convert it
		#   to UTF-8 before proxifying.
		un_utf16(\$body), $charset= 'UTF-8' if ($body=~ /^(?:\376\377|\377\376)/) ;

		# Part of workaround for Sun servers (see $may_be_swf above).
		if ($may_be_swf && $body=~ /^[FC]WS[\x01-\x09]/) {
		    $type= 'application/x-shockwave-flash' ;
		}

		# If Content-Type: is "text/html" and body looks like HTML,
		#   then treat it as HTML.  This helps with sites that play
		#   fast and loose with MIME types (e.g. hotmail).  Hacky.
		# Remove leading HTML comments before testing for text/html;
		#   e.g. hotmail puts HTML comments at start of JS resources,
		#   and even gives Content-Type as text/html .  :P
		my($leading_html_comments)= $body=~ /^(\s*(?:<!--.*-->\s*)*)/ ;
		$body= substr($body, length($leading_html_comments))
		    if $leading_html_comments ;

		if (($content_type eq 'text/html') and $body=~ /^\s*<(?:\!(?!--\s*\n)|html)/) {
		    $type= 'text/html' ;
		    $is_html= 1 ;
		    $body= $leading_html_comments . $body ;

		} else {

		    $body= (&proxify_block($body, $type))[0] ;

		    # Re-enbyte $body if needed.
		    if (defined $charset) {
			eval { $body= encode($charset, $body) } ;
			&malformed_unicode_die($charset) if $@ ;
		    }

		    # gzip the response body if we're allowed and able.
		    if ($ENV{HTTP_ACCEPT_ENCODING}=~ /\bgzip\b/i) {
			eval { require IO::Compress::Gzip } ;
			if (!$@) {
			    my $zout ;
			    IO::Compress::Gzip::gzip(\$body, \$zout)
				or HTMLdie("Couldn't gzip: $IO::Compress::Gzip::GzipError");
			    $body= $zout ;
			    $headers= "Content-Encoding: gzip\015\012" . $headers ;
			}
		    }

		    $headers=~ s/^Content-Length:.*/
				 'Content-Length: ' . length($body) /mie ;

		    print $STDOUT $status, $headers, $body ;
		    $response_sent= 1 ;
		}


	    } elsif ($is_html) {
		my($transmit_in_parts) ;
		foreach (@TRANSMIT_HTML_IN_PARTS_URLS) {
		    $transmit_in_parts= 1, last  if $URL=~ /$_/ ;
		}

		# Transmit the HTML in parts if so configured. 
		if ($transmit_in_parts) {
		    print $STDOUT $status ;
		    &transmit_html_in_parts($headers, 'S') ;

		   $response_sent= 1 ;

		} else {
		    # If response is chunked, handle as above; see comments there.
		    if ($headers=~ /^Transfer-Encoding:[ \t]*chunked\b/mi) {
			($body, $footers)= &get_chunked_body('S') ;
			&HTMLdie(&HTMLescape("Error reading chunked response from $URL ."))
			    unless defined($body) ;
			$headers=~ s/^Transfer-Encoding:[^\012]*\012?//mig ;
			$headers=~ s/^(\015\012|\012)/$footers$1/m ;

		    # Handle explicitly sized response.
		    } elsif ($headers=~ /^Content-Length:[ \t]*(\d+)/mi) {
			$body= &read_socket('S', $1) ;

		    # If not chunked or sized, read entire input into $body.
		    } else {
			undef $/ ;
			$body= <S> ;
		    }

		    shutdown(S, 0)  if $RUNNING_ON_IIS ;  # without this, IIS+MSIE hangs

		    # If $body is gzipped, then gunzip it.
		    # Change $headers to maintain consistency, even though it will
		    #   probably just be compressed again later.
		    if ($headers=~ /^Content-Encoding:.*\bgzip\b/mi) {
			eval { require IO::Uncompress::Gunzip } ;  # don't check during compilation
			&no_gzip_die if $@ ;
			my $zout ;
			IO::Uncompress::Gunzip::gunzip(\$body => \$zout)
			    or HTMLdie("Couldn't gunzip: $IO::Uncompress::Gunzip::GunzipError") ;
			$body= $zout ;
			$headers=~ s/^Content-Encoding:.*?\012//gims ;
		    }

		    # Due to a bug in (at least some) captcha systems, where they label
		    #   the test image as "text/html", we test for the image here by
		    #   examining the first 1000 chars for non-printable chars.
		    if ($env_accept=~ m#^\s*image/#i) {
			my $binchars= substr($body, 0, 1000)=~ tr/\x00-\x08\x0b\x0c\x0e-\x1b\x80-\xff/\x00-\x08\x0b\x0c\x0e-\x1b\x80-\xff/ ;
			if ($binchars > ( (length($body)<1000) ? length($body)*0.25 : 250 )) {
			    print $STDOUT $status, $headers, $body ;
			    $response_sent= 1 ;
			    close(S) ;
			    untie(*S) if $scheme eq 'https' ;
			    return ;
			}
		    }

		    if (defined $charset) {
			eval { $body= decode($charset, $body) } ;
			&malformed_unicode_die($charset) if $@ ;
		    }

		    # If $body looks like it's in UTF-16 encoding, then convert
		    #   it to UTF-8 before proxifying.
		    un_utf16(\$body), $charset= 'UTF-8' if ($body=~ /^(?:\376\377|\377\376)/) ;
		}


	    # This is for when the resource is passed straight through without
	    #   modification.
	    # We don't care whether it's chunked or not here, or gzipped or not.
	    # Except: some servers leave a persistent connection open even when
	    #   we send "Connection: close", so we must close the connection
	    #   after reading the response, so we still must be careful to read the
	    #   correct number of bytes, so we respect Content-Length: and chunked
	    #   encoding for this.
	    # Ideally, we'd use recv() to get "read all available but block until
	    #   something available" behavior, but that fails because of mixing
	    #   buffered and non-buffered input.  Also, select() doesn't work well
	    #   on buffered input, and is unreliable even on unbuffered input on
	    #   some systems.  So, the best we can do is set up a read() loop.
	    #   Note that read() blocks until the entire requested input is read,
	    #   or at EOF.
	    } else {
		my($buf) ;
		print $STDOUT $status, $headers ;

		# Use Content-Length: if available.
		if ($headers=~ /^Content-Length:[ \t]*(\d+)/mi) {
		    my $lefttoget= $1 ;
		    my $thisread ;
		    while ($lefttoget>0 and $thisread= read(S, $buf, ($lefttoget<16384) ? $lefttoget : 16384)) {
			&HTMLdie("read() error: $!")  unless defined $thisread ;
			print $STDOUT $buf ;
			$lefttoget-= $thisread ;
		    }

		# Pass through response if chunked.
		} elsif ($headers=~ /^Transfer-Encoding:[ \t]*chunked\b/mi) {
		    # Get chunks.
		    my $hex_size ;
		    while ($hex_size= <S>) {
			print $STDOUT $hex_size ;
			no warnings 'digit' ;  # to let hex() operate without warnings
			last unless $lefttoget= hex($hex_size) ;
			my $thisread ;
			while ($lefttoget>0 and $thisread= read(S, $buf, ($lefttoget<16384) ? $lefttoget : 16384)) {
			    &HTMLdie("chunked read() error: $!")  unless defined $thisread ;
			    print $STDOUT $buf ;
			    $lefttoget-= $thisread ;
			}
			print $STDOUT scalar <S> ;    # clear CRLF after chunk
		    }
		    # Get footers.
		    while (<S>) {
			print $STDOUT $_ ;
			last if /^(\015\012|\012)/  || $_ eq '' ;   # lines end w/ LF or CRLF
		    }

		# If no indication of response length, just pass all socket data through.
		} else {
		    # If using SSL, read() could return 0 and truncate data. :P
		    print $STDOUT $buf while read(S, $buf, 16384) ;
		}

		close(S) ;
		$response_sent= 1 ;
	    }

	} else {
	    $body= '' ;
	}

	close(S) ;
	untie(*S) if $scheme eq 'https' ;

    }  # HTTP_GET:

}  # sub http_get()




# This package defines a SSL filehandle, complete with all the functions
#   needed to tie a filehandle to.  This lets us use the routine http_get()
#   above for SSL (https) communication too, which means we only have one
#   routine to maintain instead of two-- big win.
# The idea was taken from Net::SSLeay::Handle, which is a great idea, but the
#   current implementation of that module isn't suitable for this application.
# This implementation uses an input buffer, which lets us write a moderately
#   efficient READLINE() routine here.  Net::SSLeay::ssl_read_until() would be
#   the natural function to use for that, but it reads and tests all input one
#   character at a time.
# This is in a BEGIN block to make sure any initialization is done.  "use"
#   would effectively do a BEGIN block too.

# These are all socket functions used by http_get():  print(), read(), <>,
#   close(), fileno() for select(), eof(), binmode()

BEGIN {
    package SSL_Handle ;

    use vars qw($SSL_CONTEXT  $DEFAULT_READ_SIZE) ;

    $DEFAULT_READ_SIZE= 512 ;   # Only used for <> style input, so doesn't need to be big.


    # Create an SSL socket with e.g. "tie(*S_SSL, 'SSL_Handle', \*S_PLAIN)",
    #   where S_PLAIN is an existing open socket to be used by S_SSL.
    # S_PLAIN must remain in scope for the duration of the use of S_SSL, or
    #   else you'll get OpenSSL errors like "bad write retry".
    # If $unbuffered is set, then the socket input will be read one character
    #   at a time (probably slower).
    sub TIEHANDLE {
	my($class, $socket, $is_server, $unbuffered)= @_ ;
	my($ssl) ;

	create_SSL_CONTEXT($is_server) ;

	$ssl = Net::SSLeay::new($SSL_CONTEXT)
	    or &main::HTMLdie("Can't create SSL connection: $!");
	Net::SSLeay::set_fd($ssl, fileno($socket))
	    or &main::HTMLdie("Can't set_fd: $!") ;

	bless { SSL      => $ssl,
		socket   => $socket,
		readsize => ($unbuffered  ? 0  : $DEFAULT_READ_SIZE),
		buf      => '',
		eof      => '',
	      },
	    $class ;  # returns reference
    }


    sub create_SSL_CONTEXT {
	my($is_server)= @_ ;

	# $SSL_CONTEXT only needs to be created once (e.g. with mod_perl or daemon).
	unless ($SSL_CONTEXT) {
	    # load_error_strings() isn't worth the effort if running as a CGI script.
	    Net::SSLeay::load_error_strings() if $main::RUN_METHOD ne 'cgi' ;
	    Net::SSLeay::SSLeay_add_ssl_algorithms() ;
	    Net::SSLeay::randomize() ;

	    # Create the reusable SSL context
	    $SSL_CONTEXT= Net::SSLeay::CTX_new()
		or &main::HTMLdie("Can't create SSL context: $!") ;

	    # Need this to cope with bugs in some other SSL implementations.
	    Net::SSLeay::CTX_set_options($SSL_CONTEXT, &Net::SSLeay::OP_ALL) ;

	    # Makes life easier if using blocking IO.  Flag 0x04 is SSL_MODE_AUTO_RETRY .
	    Net::SSLeay::CTX_set_mode($SSL_CONTEXT, 4) ;
	}

	# Set SSL key and certificate for server socket handles.
	# jsm-- must make UI for keys....
	if ($is_server) {
	    Net::SSLeay::CTX_use_RSAPrivateKey_file($SSL_CONTEXT, File::Spec->catfile($main::PROXY_DIR, $main::PRIVATE_KEY_FILE), &Net::SSLeay::FILETYPE_PEM)
		or Net::SSLeay::die_if_ssl_error("error with private key: $!") ;
	    Net::SSLeay::CTX_use_certificate_file($SSL_CONTEXT, File::Spec->catfile($main::PROXY_DIR, $main::CERTIFICATE_FILE), &Net::SSLeay::FILETYPE_PEM)
		or Net::SSLeay::die_if_ssl_error("error with certificate: $!") ;
	}
    }


    # For the print() function.  Respect $, and $\ settings.
    sub PRINT {
	my($self)= shift ;
	my($written, $errs)=
	    Net::SSLeay::ssl_write_all($self->{SSL}, join($, , @_) . $\ ) ;
	# jsm-- following line generates OpenSSL warnings... need to debug.
#	die "Net::SSLeay::ssl_write_all error: $errs"  if $errs ne '' ;
	return 1 ;   # to keep consistent with standard print()
    }


    # For read() and sysread() functions.
    # Note that unlike standard read() or sysread(), this function can return
    #   0 even when not at EOF, and when select() on the underlying socket
    #   indicates there is data to be read.  :(  This is because of SSL
    #   buffering issues: OpenSSL processes data in chunks (records), so a
    #   socket may have some data available but not enough for a full record,
    #   i.e. enough to release decrypted data to the reader.
    # So how can an application distinguish between an empty read() and EOF?
    #   Note that eof() is problematic too (see notes there).  :(
    # jsm-- may be possible to handle this by looking for SSL_ERROR_WANT_READ
    #   in the error code; http://www.openssl.org/docs/ssl/SSL_get_error.html
    #   has some info, then look in the source code of Net::SSLeay.
    sub READ {
	my($self)= shift ;
	return 0 if $self->{eof} ;

	# Can't use my(undef) in some old versions of Perl, so use $dummy.
	my($dummy, $len, $offset)= @_ ;   # $_[0] is handled explicitly below
	my($read, $errs) ;

	# this could be cleaned up....
	if ($len > length($self->{buf})) {
	    if ( $offset || ($self->{buf} ne '') ) {
		$len-= length($self->{buf}) ;
		#$read= Net::SSLeay::ssl_read_all($self->{SSL}, $len) ;
		($read, $errs)= &ssl_read_all_fixed($self->{SSL}, $len) ;
		&main::HTMLdie("ssl_read_all_fixed() error: $errs") if $errs ne '' ;
		return undef unless defined($read) ;
		$self->{eof}= 1  if length($read) < $len ;
		my($buflen)= length($_[0]) ;
		$_[0].= "\0" x ($offset-$buflen)  if $offset>$buflen ;
		substr($_[0], $offset)= $self->{buf} . $read ;
		$self->{buf}= '' ;
		return length($_[0])-$offset ;
	    } else {
		# Streamlined block for the most common case.
		#$_[0]= Net::SSLeay::ssl_read_all($self->{SSL}, $len) ;
		($_[0], $errs)= &ssl_read_all_fixed($self->{SSL}, $len) ;
		&main::HTMLdie("ssl_read_all_fixed() error: $errs") if $errs ne '' ;
		return undef unless defined($_[0]) ;
		$self->{eof}= 1  if length($_[0]) < $len ;
		return length($_[0]) ;
	    }
	} else {
	    # Here the ?: operator returns an lvar.
	    ($offset  ? substr($_[0], $offset)  : $_[0])=
		substr($self->{buf}, 0, $len) ;
	    substr($self->{buf}, 0, $len)= '' ;
	    return $len ;
	}
    }


    # For <> style input.
    # In Perl, $/ as the input delimiter can have two special values:  undef
    #   reads all input as one record, and "" means match on multiple blank
    #   lines, like the regex "\n{2,}".  Net::SSLeay doesn't support these,
    #   but here we support the undef value (though not the "" value).
    # See the note with READ(), above, about possible SSL buffering issues.
    #   It's not as big a problem here, since <> returns undef at EOF.  Note
    #   that ssl_read_all() blocks until all requested data is read.
    # Net::SSLeay::ssl_read_until() would normally be the natural function for
    #   this, but it reads and tests all input one character at a time, which
    #   is potentially very inefficient.  Thus we implement this package with
    #   an input buffer.
    sub READLINE {
	my($self)= shift ;
	my($read, $errs) ;
	if (defined($/)) {
	    if (wantarray) {
		return () if $self->{eof} ;
		($read, $errs)= &ssl_read_all_fixed($self->{SSL}) ;
		&main::HTMLdie("ssl_read_all_fixed() error: $errs") if $errs ne '' ;
		# Prepend current buffer, and split to end items on $/ or EOS;
		#   this regex prevents final '' element.
		$self->{eof}= 1 ;
		return ($self->{buf} . $read)=~ m#(.*?\Q$/\E|.+?\Z(?!\n))#sg ;
	    } else {
		return '' if $self->{eof} ;
		my($pos, $read, $ret) ;
		while ( ($pos= index($self->{buf}, $/)) == -1 ) {
		    $read= Net::SSLeay::read($self->{SSL}, $self->{readsize} || 1 ) ;
		    #return undef if $errs = Net::SSLeay::print_errs('SSL_read') ;
		    &main::HTMLdie("Net::SSLeay::read error: $errs")
			if $errs = Net::SSLeay::print_errs('SSL_read') ;
		    $self->{eof}= 1, return $self->{buf}  if $read eq '' ;
		    $self->{buf}.= $read ;
		}
		$pos+= length($/) ;
		$ret= substr($self->{buf}, 0, $pos) ;
		substr($self->{buf}, 0, $pos)= '' ;
		return $ret ;
	    }
	} else {
	    return '' if $self->{eof} ;
	    ($read, $errs)= &ssl_read_all_fixed($self->{SSL}) ;
	    &main::HTMLdie("ssl_read_all_fixed() error: $errs") if $errs ne '' ;
	    $self->{eof}= 1 ;
	    return  $self->{buf} . $read ;
	}
    }


    # Used when closing socket, or from UNTIE() or DESTROY() if needed.
    #   Calling Net::SSLeay::free() twice on the same object causes a crash,
    #   so be careful not to do that.
    sub CLOSE {
	my($self)= shift ;
	my($errs) ;
	$self->{eof}= 1 ;
	$self->{buf}= '' ;
	if (defined($self->{SSL})) {
	    Net::SSLeay::free($self->{SSL}) ;
	    delete($self->{SSL}) ;  # to detect later if we've free'd it or not
	    &main::HTMLdie("Net::SSLeay::free error: $errs")
		if $errs= Net::SSLeay::print_errs('SSL_free') ;
	    close($self->{socket}) ;
	}
    }

    # In case the SSL filehandle is not closed correctly, this will deallocate
    #   as needed.  Without this, memory could be eaten up under mod_perl.
    # Some versions of Perl seem to have trouble with the scoping of tied
    #   variables and their objects, so define both UNTIE() and DESTROY() here.
    sub UNTIE {
	my($self)= shift ;
	$self->CLOSE ;
    }
    sub DESTROY {
	my($self)= shift ;
	$self->CLOSE ;
    }


    # FILENO we define to be the fileno() of the underlying socket.
    #   This is our best guess as to what will work with select(), which is
    #   the only thing fileno() is used for here.
    # See the note with READ(), above, about possible issues with select().
    sub FILENO {
	my($self)= shift ;
	return fileno($self->{socket}) ;
    }


    # For EOF we first check the fields we set ({eof} and {buf}), then test the
    #   eof() value of the underlying socket.
    # Note that there may still be data coming through the socket even
    #   though a read() returns nothing; see the note with READ() above.
    #   It may be more accurate here to try "Net::SSLeay::read($self->{SSL},1)"
    #   into {buf} before using eof().
    # This routine causes a weird problem:  If Perl's eof() is used on a tied
    #   SSL_Handle, it causes later read()'s on that filehandle to fail with
    #   "SSL3_GET_RECORD:wrong version number", which seems inappropriate.
    #   So, avoid use of eof().  :(  Maybe test a read result against ''.
    sub EOF {
	my($self)= shift ;
	return 1 if $self->{eof} ;        # overrides anything left in {buf}
	return 0 if $self->{buf} ne '' ;
	return eof($self->{socket}) ;
    }


    # BINMODE we define to be the same as binmode() on the underlying socket.
    # Only ever relevant on non-Unix machines.
    sub BINMODE {
	my($self)= shift ;
	binmode($self->{socket}) ;
    }


    # In older versions of Net::SSLeay, there was a bug in ssl_read_all()
    #   and ssl_read_until() where pages were truncated on any "0" character.
    #   To work with those versions, here we use a fixed copy of ssl_read_all().
    #   Earlier versions of CGIProxy had older copies of the two routines but
    #   fixed; now we just copy ssl_read_all() in from the new Net::SSLeay
    #   module and tweak it as needed.  (ssl_read_until() is no longer needed
    #   now that this package uses an input buffer.)

    sub ssl_read_all_fixed {
	my ($ssl,$how_much) = @_;
	$how_much = 2000000000 unless $how_much;
	my ($got, $errs);
	my $reply = '';

	while ($how_much > 0) {
	    # read($ssl, 2000000000) would eat up memory.
	    $got = Net::SSLeay::read($ssl, ($how_much>32768) ? 32768 : $how_much);
	    last if $errs = Net::SSLeay::print_errs('SSL_read');
	    $how_much -= Net::SSLeay::blength($got);
	    last if $got eq '';  # EOF
	    $reply .= $got;
	}
	return wantarray ? ($reply, $errs) : $reply;
    }


    # end of package SSL_Handle
}




# ftp_get:

sub ftp_get {
    my($is_dir, $rcode, @r, $dataport, $remote_addr,
       $ext, $content_type, %content_type, $content_length, $enc_URL,
       @welcome, @cwdmsg) ;
    local($/)= "\012" ;

    $port= 21 if $port eq '' ;

    # List of file extensions and associated MIME types, or at least the ones
    #   a typical browser distinguishes from a nondescript file.
    # I'm open to suggestions for improving this.  One option is to read the
    #   file mime.types if it's available.
    %content_type=
	  ('txt',  'text/plain',
	   'text', 'text/plain',
	   'htm',  'text/html',
	   'html', 'text/html',
	   'css',  'text/css',
	   'png',  'image/png',
	   'jpg',  'image/jpeg',
	   'jpeg', 'image/jpeg',
	   'jpe',  'image/jpeg',
	   'gif',  'image/gif',
	   'xbm',  'image/x-bitmap',
	   'mpg',  'video/mpeg',
	   'mpeg', 'video/mpeg',
	   'mpe',  'video/mpeg',
	   'qt',   'video/quicktime',
	   'mov',  'video/quicktime',
	   'aiff', 'audio/aiff',
	   'aif',  'audio/aiff',
	   'au',   'audio/basic',
	   'snd',  'audio/basic',
	   'wav',  'audio/x-wav',
	   'mp2',  'audio/x-mpeg',
	   'mp3',  'audio/mpeg',
	   'ram',  'audio/x-pn-realaudio',
	   'rm',   'audio/x-pn-realaudio',
	   'ra',   'audio/x-pn-realaudio',
	   'gz',   'application/x-gzip',
	   'zip',  'application/zip',
	   ) ;


    $is_dir= $path=~ m#/$# ;
    $is_html= 0 if $is_dir ;   # for our purposes, do not treat dirs as HTML

    # Set $content_type based on file extension.
    # Hmm, still unsure how best to handle unknown file types.  This labels
    #   them as text/plain, so that README's, etc. will display right.
    ($ext)= $path=~ /\.(\w+)$/ ;  # works for FTP, not for URLs with query etc.
    $content_type= ($is_html || $is_dir)  ? 'text/html'
					  : $content_type{lc($ext)}
					    || 'text/plain' ;


    # If we're removing scripts, then disallow script MIME types.
    if ($scripts_are_banned_here) {
	&script_content_die if $content_type=~ /^$SCRIPT_TYPE_REGEX$/io ;
    }


    # Hack to help handle spaces in pathnames.  :P
    # $path should be delivered to us here with spaces encoded as "%20".
    #   But that's not what the FTP server wants (or what we should display),
    #   so translate them back to spaces in a temporary copy of $path.
    #   Hopefully the FTP server will allow spaces in the FTP commands below,
    #   like "CWD path with spaces".
    local($path)= $path ;
    $path=~ s/%20/ /g ;


    # Create $status and $headers, and leave $body and $is_html as is.
    # Directories use an HTML response, though $is_html is false when $is_dir.
    $status= "$HTTP_1_X 200 OK\015\012" ;
    $headers= $session_cookies . $NO_CACHE_HEADERS . "Date: " . &rfc1123_date($now,0) . "\015\012"
	. ($content_type  ? "Content-type: $content_type\015\012"  : '') . "\015\012" ;


    # Open the control connection to the FTP server
    &newsocketto('S', $host, $port) ;
    binmode S ;   # see note with "binmode STDOUT", above

    # Luckily, RFC 959 (FTP) has a really good list of all possible response
    #   codes to all possible commands, on pages 50-53.

    # Connection establishment
    ($rcode)= &ftp_command('', '120|220') ;
    &ftp_command('', '220') if $rcode==120 ;

    # Login
    ($rcode, @welcome)= &ftp_command("USER $username\015\012", '230|331') ;
    ($rcode, @welcome)= &ftp_command("PASS $password\015\012", '230|202')
	if $rcode==331 ;

    # Set transfer parameters
    &ftp_command("TYPE I\015\012", '200') ;


    # If using passive FTP, send PASV command and parse response.  RFC 959
    #   isn't clear on the response format, but here we assume that the first
    #   six integers separated by commas are the host and port.
    if ($USE_PASSIVE_FTP_MODE) {
	my(@p) ;
	($rcode, @r)= &ftp_command("PASV\015\012", '227') ;
	@p= (join('',@r))=~
		/(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)/ ;
	$dataport= ($p[4]<<8) + $p[5] ;

	# Open the data socket to $dataport.  This is conceptually paired
	#   with the accept() for non-passive mode below, but we have to
	#   open the socket here first to allow for 125/150 responses to
	#   LIST and RETR commands in passive mode.
	&newsocketto('DATA_XFER', $host, $dataport) ;
	binmode DATA_XFER ;   # see note with "binmode STDOUT", above

    # If not using passive FTP, listen on open port and send PORT command.
    # See notes by newsocketto() about replacing pack('S n a4 x8') usage.
    } else {
	# Create and listen on data socket
	socket(DATA_LISTEN, AF_INET, SOCK_STREAM, (getprotobyname('tcp'))[2])
	    || &HTMLdie("Couldn't create FTP data socket: $!") ;
#	bind(DATA_LISTEN, pack('S n a4 x8', AF_INET, 0, "\0\0\0\0") )
	bind(DATA_LISTEN, pack_sockaddr_in(0, INADDR_ANY))
	    || &HTMLdie("Couldn't bind FTP data socket: $!") ;
#	$dataport= (unpack('S n a4 x8', getsockname(DATA_LISTEN)))[1] ;
	$dataport= (unpack_sockaddr_in(getsockname(DATA_LISTEN)))[0] ;
	listen(DATA_LISTEN,1)
	    || &HTMLdie("Couldn't listen on FTP data socket: $!") ;
	select((select(DATA_LISTEN), $|=1)[0]) ;    # unbuffer the socket

	# Tell FTP server which port to connect to
	&ftp_command( sprintf("PORT %d,%d,%d,%d,%d,%d\015\012",
			      unpack('C4', substr(getsockname(S),4,4)),
			      $dataport>>8, $dataport & 255),
		      '200') ;
    }


    # Do LIST for directories, RETR for files.
    # Unfortunately, the FTP spec in RFC 959 doesn't define a standard format
    #   for the response to LIST, but most servers use the equivalent of
    #   Unix's "ls -l".  Response to the NLST command is designed to be
    #   machine-readable, but it has nothing but file names.  So we use
    #   LIST and parse it as best we can later.
    if ($is_dir) {
	# If we don't CWD first, then symbolic links won't be followed.
	($rcode, @cwdmsg)= &ftp_command("CWD $path\015\012", '250') ;
	($rcode, @r)= &ftp_command("LIST\015\012", '125|150') ;
# was:  ($rcode, @r)= &ftp_command("LIST $path\015\012", '125|150') ;

    } else {
	($rcode, @r)= &ftp_command("RETR $path\015\012", '125|150|550') ;

	# If 550 response, it may be a symlink to a directory.
	# Try to CWD to it; if successful, do a redirect, else die with the
	#   original error response.  Note that CWD is required by RFC 1123
	#   (section 4.1.2.13), which updates RFC 959.
	if ($rcode==550) {
	    ($rcode)= &ftp_command("CWD $path\015\012", '') ;
	    &ftp_error(550,@r) unless $rcode==250 ;

	    ($enc_URL= $URL)=~ s/ /%20/g ;  # URL-encode any spaces

	    # Redirect the browser to the same URL with a trailing slash
	    print $STDOUT "$HTTP_1_X 301 Moved Permanently\015\012",
			  $session_cookies, $NO_CACHE_HEADERS,
			  "Date: ", &rfc1123_date($now,0), "\015\012",
			  "Location: ", $url_start, &wrap_proxy_encode($enc_URL . '/'),
			  "\015\012\015\012" ;
	    close(S) ; close(DATA_LISTEN) ; close(DATA_XFER) ;
	    goto ONE_RUN_EXIT ;
	}
    }


    # If not using passive FTP, accept the connection.
    if (!$USE_PASSIVE_FTP_MODE) {
	($remote_addr= accept(DATA_XFER, DATA_LISTEN))
	    || &HTMLdie("Error accepting FTP data socket: $!") ;
	select((select(DATA_XFER), $|=1)[0]) ;      # unbuffer the socket
	close(DATA_LISTEN) ;
	&HTMLdie("Intruder Alert!  Someone other than the server is trying "
	       . "to send you data.")
	    unless (substr($remote_addr,4,4) eq substr(getpeername(S),4,4)) ;
    }


    # Read the data into $body.
    # Streaming support added in 1.3.  For notes about streaming, look near
    #   the end of the http_get() routine.  Basically, as long as a resource
    #   isn't HTML (or a directory listing, in the case of FTP), we can pass
    #   the data immediately to the client, since it won't be modified.  Be
    #   sure to set $response_sent here.

    # This first block is for the rare case when an FTP resource is a special
    #   type that needs to be converted, e.g. a style sheet.  The block is
    #   copied in from http_get() and modified.  It will be cleaner and
    #   handled differently in a future version.

    if ( !$is_dir && !$is_html &&
	 (    ($expected_type=~ /^$TYPES_TO_HANDLE_REGEX$/io)
	   || ($content_type=~  /^$TYPES_TO_HANDLE_REGEX$/io)   ) ) {

	my($type) ;
	if ( ($expected_type eq 'text/css') || ($content_type eq 'text/css') ) {
	    $type= 'text/css' ;
	} elsif ($expected_type=~ /^$TYPES_TO_HANDLE_REGEX$/io) {
	    $type= $expected_type ;
	} else {
	    $type= $content_type ;
	}

	undef $/ ;
	$body= <DATA_XFER> ;
	$body= (&proxify_block($body, $type))[0] ;

	$headers= "Content-Length: " . length($body) . "\015\012" . $headers ;

	print $STDOUT $status, $headers, $body ;
	$response_sent= 1 ;


    } elsif ($is_html) {
	undef $/ ;
	$body= <DATA_XFER> ;

    } elsif ($is_dir) {
	undef $/ ;            # This was used for all non-HTML before streaming
	$body= <DATA_XFER> ;  #   was supported.

    } else {

	# Stick a Content-Length: header into the headers if appropriate (often
	#   there's a "(xxx bytes)" string in a 125 or 150 response line).
	# Be careful about respecting previous value of $headers, which may
	#   already end in a blank line.
	foreach (grep(/^(125|150)/, @r)) {
	    if ( ($content_length)= /\((\d+)[ \t]+bytes\)/ ) {
		$headers= "Content-Length: $content_length\015\012" .$headers ;
		last ;
	    }
	}

	# This is the primary change to support streaming media.
	my($buf) ;
	print $STDOUT $status, $headers ;
	print $STDOUT $buf while read(DATA_XFER, $buf, 16384) ;
	$response_sent= 1 ;

    }


    close(DATA_XFER) ;

    # Get the final completion response
    &ftp_command('', '226|250') ;

    &ftp_command("QUIT\015\012") ;   # don't care how they answer

    close(S) ;

    # Make a user-friendly directory listing.  Add Content-Length: header.
    if ($is_dir) {
	&ftp_dirfix(\@welcome, \@cwdmsg) ;
	$headers= "Content-Length: " . length($body) . "\015\012" . $headers ;
    }

}  # sub ftp_get()


# Send $cmd and return response code followed by full lines of  FTP response.
# Die if response doesn't match the regex $ok_response.
# Assumes the FTP control connection is in socket S.
sub ftp_command {
    my($cmd, $ok_response)= @_ ;
    my(@r, $rcode) ;
    local($/)= "\012" ;

    print S $cmd ;

    $_= $r[0]= <S> ;
    $rcode= substr($r[0],0,3) ;
    until (/^$rcode /) {      # this catches single- and multi-line responses
	push(@r, $_=<S>) ;
    }

    &ftp_error($rcode,@r) if $ok_response ne '' && $rcode!~ /$ok_response/ ;
    return $rcode, @r ;
}


# Convert a directory listing to user-friendly HTML.
# The text in $body is the output of the FTP LIST command, which is *usually*
#   the equivalent of Unix's "ls -l" command.  See notes in ftp_get() about
#   why we use LIST instead of NLST.
# A couple of tangles here to handle spaces in filenames.  We should probably
#   handle spaces in other protocols too, but URLs normally prohibit spaces--
#   it's only relative paths within a scheme (like FTP) that would have them.
sub ftp_dirfix {
    my($welcome_ref, $cwdmsg_ref)= @_ ;
    my($newbody, $parent_link, $max_namelen,
       @f, $is_dir, $is_link, $link, $name, $size, $size_type, $file_type,
       $welcome, $cwdmsg, $insertion, $enc_path) ;

    # Set minimum name column width; longer names will widen the column
    $max_namelen= 16 ;

    # each file should have name/, size, date
    my(@body)= split(/\015?\012/, $body) ;
    foreach (@body) {
	# Hack to handle leading spaces in filenames-- only allow a single
	#   space after the 8th field before filename starts.
#	@f= split(" ", $_, 9) ;   # Note special use of " " pattern.
#	next unless $#f>=8 ;
	@f= split(" ", $_, 8) ;   # Note special use of " " pattern.
	next unless $#f>=7 ;
	@f[7,8]= $f[7]=~ /^(\S*) (.*)/ ;  # handle leading spaces in filenames

	next if $f[8]=~ /^\.\.?$/ ;
	$file_type= '' ;
	$is_dir=  $f[0]=~ /^d/i ;
	$is_link= $f[0]=~ /^l/i ;
	$file_type= $is_dir     ? 'Directory'
		  : $is_link    ? 'Symbolic link'
		  :               '' ;
	$name= $f[8] ;
	$name=~ s/^(.*) ->.*$/$1/ if $is_link ;   # remove symlink's " -> xxx"
	$name.= '/' if $is_dir ;
	$max_namelen= length($name) if length($name)>$max_namelen ;
	if ($is_dir || $is_link) {
	    ($size, $size_type)= () ;
	} else {
	    ($size, $size_type)= ($f[4], 'bytes') ;
	    ($size, $size_type)= ($size>>10, 'Kb') if $size > 10240 ;
	}

	# Easy absolute URL calculation, because we know it's a relative path.
	($enc_path= $base_path . $name)=~ s/ /%20/g ;  # URL-encode any spaces
	$link=  &HTMLescape( $url_start . &wrap_proxy_encode($enc_path) ) ;

	$newbody.=
	    sprintf("  <a href=\"%s\">%s</a>%s %5s %-5s %3s %2s %5s  %s\012",
			   $link, $name, "\0".length($name),
			   $size, $size_type,
			   @f[5..7],
			   $file_type) ;
    }

    # A little hack to get filenames to line up right-- replace embedded
    #  "\0"-plus-length with correct number of spaces.
    $newbody=~ s/\0(\d+)/ ' ' x ($max_namelen-$1) /ge ;

    if ($path eq '/') {
	$parent_link= '' ;
    } else {
	($enc_path= $base_path)=~ s#[^/]*/$## ;
	$enc_path=~ s/ /%20/g ;  # URL-encode any spaces
	$link=  &HTMLescape( $url_start . &wrap_proxy_encode($enc_path) ) ;
	$parent_link= "<a href=\"$link\">Up to higher level directory</a>" ;
    }

    if ($SHOW_FTP_WELCOME && $welcome_ref) {
	$welcome= &HTMLescape(join('', grep(s/^230-//, @$welcome_ref))) ;
	# Make links of any URLs in $welcome.  Imperfect regex, but does OK.
	$welcome=~ s#\b([\w+.-]+://[^\s"']+[\w/])(\W)#
	    '<a href="' . &full_url($1) . "\">$1</a>$2" #ge ;
	$welcome.= "<hr>" if $welcome ne '' ;
    } else {
	$welcome= '' ;
    }

    # If CWD returned a message about this directory, display it.  Make links
    #   a la $welcome, above.
    if ($cwdmsg_ref) {
	$cwdmsg= &HTMLescape(join('', grep(s/^250-//, @$cwdmsg_ref))) ;
	$cwdmsg=~ s#\b([\w+.-]+://[^\s"']+[\w/])(\W)#
	    '<a href="' . &full_url($1) . "\">$1</a>$2" #ge ;
	$cwdmsg.= "<hr>" if $cwdmsg ne '' ;
    }


    # Create the top insertion if needed.
    $insertion= &full_insertion($URL,0)  if $doing_insert_here ;


    $body= <<EOS ;
<html>
<title>FTP directory of $URL</title>
<body>
$insertion
<h1>FTP server at $host</h1>
<h2>Current directory is $path</h2>
<hr>
<pre>
$welcome$cwdmsg
$parent_link
$newbody
</pre>
<hr>
</body>
</html>
EOS

}


# Return a generalized FTP error page.
# For now, respond with 200.  In the future, give more appropriate codes.
sub ftp_error {
    my($rcode,@r)= @_ ;

    close(S) ; close(DATA_LISTEN) ; close(DATA_XFER) ;

    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR ;
<html>
<head><title>FTP Error</title></head>
<body>
<h1>FTP Error</h1>
<h3>The FTP server at $host returned the following error response:</h3>
<pre>
EOR
    $response.= join('', @r, "</pre>\n") . footer() ;
    my $cl= length($response) ;
    print $STDOUT <<EOR . $response;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOR

    goto ONE_RUN_EXIT ;
}



sub handle_http_request {
    my($SS, $listen_port, $apply_ssl, $out_fh, $read_address)= @_ ;
    my($remote_address) ;

    # Exit when the socket is closed on the other end.
    $SIG{PIPE}= sub { exit(1) } ;

    if ($apply_ssl) {
	my $ssl_obj= tie(*SSL2CLIENT, 'SSL_Handle', \*$SS, 1) ;

	# Rewire STDIN and STDOUT to be SSL2CLIENT .
	# Oddly, after doing this, reading from STDIN gives encrypted characters,
	#   but reading from SSL2CLIENT gives correct characters.
	# Easier to just use $STDIN.
	#close(STDIN) ;
	#open(STDIN, '+<&', \*SSL2CLIENT)  or die "rewire STDIN failed: $!\n" ;
	$STDIN= \*SSL2CLIENT ;

	# Next two lines die with a "scalar.xs:50: PerlIOScalar_pushed: Assertion ... failed"
	#   error.
	#close(STDOUT) ;
	#open(STDOUT, '+>&', \*SSL2CLIENT)  or die "rewire STDOUT failed: $!\n" ;
	$STDOUT= \*SSL2CLIENT ;

	# Accept SSL connection.
	#Net::SSLeay::accept($ssl_obj->{SSL}) or Net::SSLeay::die_if_ssl_error("SSL accept() error: $!");
#$Net::SSLeay::trace= 1 ;
	my $rv ;
	while (1) {
	    # jsm-- busy loop here-- fix.
	    $rv= Net::SSLeay::accept($ssl_obj->{SSL}) ;
	    last if $rv>0 ;
	    my $err= Net::SSLeay::get_error($ssl_obj->{SSL}, $rv) ;
	    next if $err==Net::SSLeay::ERROR_WANT_READ() or $err==Net::SSLeay::ERROR_WANT_WRITE() ;
	    return if $rv==0 and $err==Net::SSLeay::ERROR_SYSCALL() ;  # EOF that violates protocol
	    die "Net::SSLeay::accept() failed; err=[$err]\n" ;
	}

	# SSL connection is now set up.

    # Else we're using unencrypted pipes.
    } else {
	$STDIN= $SS ;
	$STDOUT= $out_fh || $SS ;
    }

    local($/)= "\012" ;

    # Support HTTP/1.1 pipelining.
    while (1) {
	my $request_line= <$STDIN> ;
	return unless defined $request_line ;

	# If line starts with a digit, it's the remote IP address.
	# A valid HTTP request line doesn't start with a digit.
	chomp($remote_address= $request_line), next  if $request_line=~ /^\d/ ;

	my($method, $request_uri, $client_http_version)=
	    $request_line=~ /^(\w+)\s+(.*)\s+(HTTP\/[\d.]+)\015?\012\z/s ;

	$request_uri=~ s#(?:^[\w+.-]+:)?//(?:[^/]*)## ;    # strip leading scheme and host:port if there


	# Read headers into @headers .
	my($header, @headers) ;
	while (($header= <$STDIN>)!~ /^\015?\012\z/) {
	    $header=~ s/\015?\012\z// ;    # remove trailing CRLF
	    last unless $header ne '' ;
	    # Unfold long headers as needed.
	    if ($header=~ s/^\s+/ / and @headers) {
		$headers[$#headers].= $header ;
	    } else {
		push(@headers, $header) ;
	    }
	}

	# For now, don't return any favicon.ico .
	if ($request_uri eq '/favicon.ico') {
	    my($date_header)= &rfc1123_date($now, 0) ;
	    print $STDOUT "HTTP/1.1 404 Not Found\015\012Date: $date_header\015\012\015\012" ;
	    next ;
	}


	# Set %ENV .
	%ENV= %ENV_UNCHANGING ;
	my($name, $value) ;
	foreach (@headers) {
	    ($name, $value)= split(/:\s*/, $_, 2) ;
	    $name=~ s/-/_/g ;
	    $ENV{'HTTP_' . uc($name)}= $value ;
	}
	foreach (qw(CONTENT_LENGTH CONTENT_TYPE)) {
	    $ENV{$_}= $ENV{"HTTP_$_"} ;
	    delete $ENV{"HTTP_$_"} ;
	}
	my $auth= $ENV{HTTP_AUTHORIZATION} ;
	delete $ENV{HTTP_AUTHORIZATION} ;

	# Set AUTH_TYPE, and authenticate!
	my($up64, $u, $p) ;
	if ($auth) {
	    ($ENV{AUTH_TYPE}, $up64)= split(/\s+/, $auth) ;
	    ($u, $p)= split(/:/, unbase64($up64))  if defined $up64 ;
	} else {
	    $ENV{AUTH_TYPE}= '' ;
	}
	return_401_response($client_http_version), last  unless &daemon_authenticate($ENV{AUTH_TYPE}, $u, $p) ;

	$ENV{PATH_INFO}= $request_uri ;
	# Skip PATH_TRANSLATED; it's messy and we don't use it.
	$ENV{REMOTE_ADDR}= $remote_address ;
	# Skip REMOTE_HOST; it's expensive and we don't use it.
	$ENV{REMOTE_USER}= $u ;
	$ENV{REQUEST_METHOD}= $method ;
	$ENV{SERVER_PROTOCOL}= $client_http_version ;


	# Run it!
	eval { one_run() } ;
	if ($@=~ /^exiting\b/) {
	    close(S) ;
	    untie(*S) ;
	    eval { alarm(0) } ;   # use eval{} to avoid failing where alarm() is missing
	    last ;
	}


	# Return if not pipelining.
	last if $ENV{HTTP_CONNECTION} eq 'close' ;
    }

    return 1 ;
}


# These are the CGI environment variables that don't change from run to run.
sub set_ENV_UNCHANGING {
    my($port)= @_ ;

    $ENV_UNCHANGING{GATEWAY_INTERFACE}= 'CGI/1.1' ;
    ($ENV_UNCHANGING{SERVER_NAME}= hostfqdn()) =~ s/\.$// ;   # bug in hostfqdn() may leave trailing dot
    $ENV_UNCHANGING{SERVER_PORT}= $port ;
    $ENV_UNCHANGING{SERVER_SOFTWARE}= 'Embedded' ;

    $ENV_UNCHANGING{QUERY_STRING}= '' ;    # it's in PATH_INFO instead.
    $ENV_UNCHANGING{SCRIPT_NAME}= '' ;
}


# Very simple for now, but may be expanded later.
sub daemon_authenticate {
    my($authtype, $u, $p)= @_ ;
    return 1 unless $EMB_USERNAME ne '' or $EMB_PASSWORD ne '' ;
    return ($u eq $EMB_USERNAME and $p eq $EMB_PASSWORD) ;
}



# This should be passed as a parameter to spawn_generic_server() (which
#   handles all listening, forking, etc.) to spawn our RTMP proxy.  This
#   routine should handle one RTMP connection and then exit.
# This routine tries to handle each chunk and message as quickly as possible,
#   including handling partial messages as the parts arrive.
# jsm-- structure of this isn't the cleanest.
sub rtmp_proxy {
    my($SS, $listen_port)= @_ ;
    $RTMP_SERVER_PORT= $listen_port ;   # hacky...

    # First, do the handshake with the client.
    
    # Store our epoch.
    my $t0_SS= [gettimeofday] ;
    my $t0_SC ;

    # Read C0 (RTMP version).
    my $c0= read_socket($SS, 1) ;

    # Send S0.
    print $SS "\x03" ;

    # Read C1 (timestamp, zero, and 1528 random bytes).
    my $c1= read_socket($SS, 1536) ;
    my $c1_read_t= int(tv_interval($t0_SS)*1000) ;    # in milliseconds
    my $client_t0= unpack('N', substr($c1, 0, 4)) ;
    my $remote1528= substr($c1, 8) ;

    # Send S1.
    my $local1528= join('', map {chr(int(rand 256))} 1..1528) ;
    print $SS pack('N', int(tv_interval($t0_SS)*1000)), "\0\0\0\0", $local1528 ;

    # Read C2 (mostly echo of S1 ).
    my $c2= read_socket($SS, 1536) ;
    die "Bad RTMP handshake" unless substr($c2, 0, 4) eq "\0\0\0\0" and substr($c2, 8) eq $local1528 ;

    # Send S2 (mostly echo of C1).
    print $SS substr($c1, 0, 4), pack('N', $c1_read_t), substr($c1, 8) ;

    # RTMP handshake with client complete.

    # Use parent process to handle client-to-server communication, and child
    #   to handle server-to-client communication.  fork() is later, inside
    #   the chunk-handling while loop.  Not the most efficient and a bit hacky,
    #   but works for now.
    my($SC, $SR, $SW) ;     # client socket, reading socket, and writing socket.
    $SR= $SS ;

    # Next, read each chunk, proxify/unproxify messages if needed, and write
    #   to other side.

    my $chunk_size= 128 ;     # default
    my($win_ack_size, $peer_win_ack_size) ;      # default???
    my $received_bytes= 0 ;   # for Acknowledgement messages

    my($cin, $b1, $b2, $b3, $b23, $fmt, $csid, $cmh, $ts, $ext_ts,
       $msg_len, $msg_type, $msg_stream_id, $is_parent) ;
    my($c, $m)= ({}, {}) ;   # hashes of chunks and messages
    while (1) {

	# Read chunk basic header.
	$b1= ord(read_socket($SR, 1)) ;
	$cin= chr($b1) ;
	($fmt, $csid)= ($b1>>6, $b1&0x3f) ;
	if ($csid==0) {
	    $cin.= $b2= read_socket($SR, 1) ;
	    $csid= ord($b2) + 64 ;
	} elsif ($csid==1) {
	    $cin.= $b23= read_socket($SR, 2) ;
	    my($b2, $b3)= unpack('C2', $b23) ;
	    $csid= $b3*256 + $b2 + 64 ;
	}

	# Create chunk list if not already created.
	$c->{$csid}{chunks}= []  unless $c->{$csid}{chunks} ;

	# Read chunk message header (none for $fmt==3).
	if ($fmt==0) {
	    $cin.= $cmh= read_socket($SR, 11) ;
	    $ts= substr($cmh, 0, 3) ;
	    @{$c->{$csid}}{qw(mlen mtype msid)}=
		(unpack('N', "\0".substr($cmh, 3, 3)),
		 ord(substr($cmh, 6, 1)),
		 unpack('V', substr($cmh, 7)) ) ;
	} elsif ($fmt==1) {
	    $cin.= $cmh= read_socket($SR, 7) ;
	    $ts= substr($cmh, 0, 3) ;
	    @{$c->{$csid}}{qw(mlen mtype)}=
		(unpack('N', "\0".substr($cmh, 3, 3)),
		 ord(substr($cmh, 6)) ) ;
	} elsif ($fmt==2) {
	    $cin.= $ts= $cmh= read_socket($SR, 3) ;
	}
	my $msid= $c->{$csid}{msid} ;

	# To multiplex messages within one chunk stream, must save mleft for
	#   each message stream.
	$c->{$csid}{mleft}{$msid}= $c->{$csid}{mlen}  unless defined $m->{$msid}{type} ;

	# Read extended timestamp, if needed.
	if ($ts eq "\xff\xff\xff") {
	    # Extended timestamp seems to be uint32, though is undocumented.
	    $cin.= $ext_ts= read_socket($SR, 4) ;
	}


	# Done reading chunk header; next, read data into message buffer or
	#   message payload.

	my $cpayload= read_socket($SR, $c->{$csid}{mleft}{$msid} <= $chunk_size
				     ? $c->{$csid}{mleft}{$msid}  : $chunk_size ) ;
	$cin.= $cpayload ;
	$c->{$csid}{mleft}{$msid}-= length($cpayload) ;
	$m->{$msid}{complete}= 1  if $c->{$csid}{mleft}{$msid}==0 ;

	# Send acknowledgement if needed.
	# jsm-- can we count on getting complete chunks?
	$received_bytes+= length($cin) ;
	if ($received_bytes>=$win_ack_size) {
	    send_acknowledgement($SR, $received_bytes, $t0_SS) ;
	    $received_bytes= 0 ;    # jsm-- do we send total bytes or bytes since last ack?
	}

	# End processing and print chunk if passthru.
	print $SW ($cin), next  if $m->{$msid}{passthru} ;

	if (!defined $m->{$msid}{type}) {
	    $m->{$msid}{mbuf}.= $cpayload ;
	} else {
	    $m->{$msid}{payload}.= $cpayload ;
	}

	# Save complete chunks, in case we just need a pass-through.
	push(@{$c->{$csid}{chunks}}, $cin) ;

	# Initialize $m element if we have full message header.
	if (!defined $m->{$msid}{type} and length($m->{$msid}{mbuf})>=11) {
	    @{$m->{$msid}}{qw(type len ts msid payload)}=
		(unpack('C', substr($m->{$msid}{mbuf}, 0, 1)),
		 unpack('N', "\0".substr($m->{$msid}{mbuf}, 1, 3)),
		 unpack('N', substr($m->{$msid}{mbuf}, 4, 4)),
		 unpack('N', "\0".substr($m->{$msid}{mbuf}, 8, 3)),
		 substr($m->{$msid}{mbuf}, 11) ) ;
	    delete $m->{$msid}{mbuf} ;
	}

	# Chunk stream ID==2 means a protocol control message.
	if ($csid==2) {

	    # Require a complete message to process protocol control messages.
	    if ($m->{$msid}{complete}) {
		die("Invalid message stream ID [$msid] in RTMP stream") unless $msid==0 ;
		my($mtype, $payload)= @{$m->{0}}{qw(type payload)} ;

		# Set chunk size
		if ($mtype==1) {
		    $chunk_size= unpack('N', $payload) ;

		# Abort message
		} elsif ($mtype==2) {
		    delete $m->{$c->{unpack('N', $payload)}{msid}} ;
		    # jsm-- need to delete part of %$c too?

		# Acknowledgement
		} elsif ($mtype==3) {
		    my $seqno= unpack('N', $payload) ;

		# User control message can pass through
		} elsif ($mtype==4) {
		    if (defined $SW) {
			print $SW @{$c->{2}{chunks}} ;
			$c->{2}{chunks}= [] ;
		    }

		# Window acknowledgement size
		# Done by server after successful connect request from client,
		#   or by either after receiving Set Peer Bandwidth message.
		# Must handle this separately for client and server, since we change data length.
		# Pass through these messages, since window size should be similar
		#   for both connections.
		} elsif ($mtype==5) {
		    $win_ack_size= unpack('N', $payload) ;
		    if (defined $SW) {
			print $SW @{$c->{2}{chunks}} ;
			$c->{2}{chunks}= [] ;
		    }

		# Set peer bandwidth
		# Pass through these messages, since window size should be similar
		#   for both connections.
		} elsif ($mtype==6) {
		    my($new_peer_was, $limit_type)=
			(unpack('N', substr($payload, 0, 4)),
			 unpack('C', substr($payload, 4)) ) ;
		    if ($new_peer_was!=$peer_win_ack_size) {
			$peer_win_ack_size= $new_peer_was ;
			send_win_ack_size($SR, $peer_win_ack_size, $is_parent ? $t0_SC : $t0_SS) ;
		    }
		    if (defined $SW) {
			print $SW @{$c->{2}{chunks}} ;
			$c->{2}{chunks}= [] ;
		    }

		} else {
		    die("Illegal PCM message type [$mtype] in RTMP stream") ;
		}

		delete $m->{0} ;
		delete $c->{2} ;
	    }


	# Otherwise, handle message piece depending on its type.  All are just
	#   pass-through except command messages, and possibly a submessage
	#   within an aggregate message.
	} else {
	    my $mtype= $m->{$msid}{type} ;

	    # Command message using AMF0 or AMF3
	    if ($mtype==20 or $mtype==17) {
		if ($m->{$msid}{complete}) {
		    ($host, $port)= ('', '') ;   # hacky
		    # Note use of $reverse parameter, true when client-to-server.
		    my $newmpl= ($mtype==20) ? proxify_RTMP_command_AMF0(\$m->{$msid}{payload}, $is_parent)
					     : proxify_RTMP_command_AMF3(\$m->{$msid}{payload}, $is_parent) ;
		    if (defined $newmpl) {

			# If $host set and in parent process, then connect to
			#   the destination server and do the handshake.
			# This is hacky, but we can only start the server connection
			#   after we've started processing messages from the client.
			if ($host and !defined $SC) {
			    $SC= rtmp_connect_to($host, $port) ;
			    $t0_SC= [gettimeofday] ;
			    $is_parent= fork() ;
			    ($SR, $SW)= $is_parent  ? ($SS, $SC)  : ($SC, $SS) ;
			    ($c, $m)= ({}, {}), next unless $is_parent ;  # restart loop if new child
			}

			my($newcbh, $newcmh0, $i) ;
			my $newm= chr($mtype)
				. substr(pack('N', length($newmpl)), 1, 3)
				. pack('N', $m->{$msid}{ts})
				. substr(pack('N', $msid), 1, 3)
				. $newmpl ;

			# Build chunk basic header.
			if ($csid<=63) {
			    $newcbh= chr($csid) ;
			} elsif ($csid<=319) {
			    $newcbh= "\0" . chr($csid-64) ;
			} else {
			    $newcbh= "\x01" . chr(($csid-64) & 0xff) . chr(($csid-64)>>8) ;
			}

			# Build chunk message header, possibly including extended timestamp.
			$newcmh0= $ts
				. substr(pack('N', length($newm)), 1, 3)
				. chr($mtype)
				. pack('V', $msid) ;
			$newcmh0.= $ext_ts if $ts eq "\xff\xff\xff" ;
			
			# Print new chunk(s) from $newm, a 0-type followed by 3-types.
			print $SW $newcbh, $newcmh0, substr($newm, 0, $chunk_size) ;
			substr($newcbh, 0, 1)||= "\xc0" ;   # set chunk fmt to 3 henceforth
			print $SW $newcbh, substr($newm, $_*$chunk_size, $chunk_size)
			    for 1..int((length($newm)-1)/$chunk_size) ;
			# Perl doesn't like line below....
			#   for ($i= $chunk_size ; $i<length($newm) ; $i+= $chunk_size) ;

		    # If new message payload is unchanged, then pass through chunks.
		    } elsif (defined $SW) {
			print $SW @{$c->{$csid}{chunks}} ;
			$c->{$csid}{chunks}= [] ;
		    }
		    delete $m->{$msid} ;
		}

	    # Aggregate message
	    } elsif ($mtype==22) {
		# jsm-- must implement

	    # Data message using AMF0 or AMF3, shared object message using
	    #   AMF0 or AMF3, audio message, or video message
	    } elsif (chr($mtype)=~ /[\x12\x0f\x13\x10\x08\x09]/) {
		print $SW @{$c->{$csid}{chunks}} ;
		$c->{$csid}{chunks}= [] ;
		$m->{$msid}{passthru}= 1 ;

	    } else {
		die("Illegal message type [$mtype] in RTMP stream") ;
	    }
	}
    }

    exit(0) ;
}   # rtmp_proxy



# Open an RTMP connection to the given host and port, and perform the handshake.
# Returns the open socket.
sub rtmp_connect_to {
    my($host, $port)= @_ ;
    $port= 1935  if $port eq '' ;
    my $S ;   # filehandle for socket

    &newsocketto($S, $host, $port) ;

    # Send C0 and C1 chunks.
    print $S "\x03" ;     # C0 is RTMP version

    # C1 is timestamp, zero, and 1528 bytes of random data.
    my $local1528= join('', map {chr(int(rand 256))} 1..1528) ;
    my $t0= [gettimeofday] ;
    print $S "\0\0\0\0\0\0\0\0", $local1528 ;

    # Read S0 and S1 chunks.
    my $s0s1= read_socket($S, 1537) ;
    my $s0s1_time= pack('N', int(tv_interval($t0)*1000)) ;
    my $remote1528= substr($s0s1, 9) ;

    # Send C2 chunk.
    print $S substr($s0s1, 1, 4), $s0s1_time, $remote1528 ;

    # Read S2 chunk.
    my $s2= read_socket($S, 1536) ;
    die "Bad RTMP handshake" unless $local1528 eq substr($s2, 8) ;

    return $S ;
}


sub send_win_ack_size {
    my($S, $win_ack_size, $t0)= @_ ;

    my $ts= int(tv_interval($t0)*1000) ;
    my $ext_ts ;

    my $msg= "\x05\0\0\x04" . pack('N', $ts) . "\0\0\0" . pack('N', $win_ack_size) ;

    if ($ts>=0xffffff) {
	$ext_ts= pack('N', $ts-0xffffff) ;
	$ts= "\xff\xff\xff" ;
    } else {
	$ts= substr(pack('N', $ts), 1, 3) ;
	$ext_ts= '' ;
    }
    print $S "\x02" . $ts . "\0\0\x0f\x05\0\0\0\0" . $ext_ts . $msg ;   # chunk header plus message
}


# Identical to send_win_ack_size() except for message type byte (in two places).
sub send_acknowledgement {
    my($S, $seqno, $t0)= @_ ;

    my $ts= int(tv_interval($t0)*1000) ;
    my $ext_ts ;

    my $msg= "\x03\0\0\x04" . pack('N', $ts) . "\0\0\0" . pack('N', $seqno) ;

    if ($ts>=0xffffff) {
	$ext_ts= pack('N', $ts-0xffffff) ;
	$ts= "\xff\xff\xff" ;
    } else {
	$ts= substr(pack('N', $ts), 1, 3) ;
	$ext_ts= '' ;
    }
    print $S "\x02" . $ts . "\0\0\x0f\x03\0\0\0\0" . $ext_ts . $msg ;   # chunk header plus message
}



# The next two routines follow the AMF0 and AMF3 specs at:
#   http://opensource.adobe.com/wiki/download/attachments/1114283/amf0_spec_121207.pdf
#   http://opensource.adobe.com/wiki/download/attachments/1114283/amf3_spec_05_05_08.pdf


# Returns the proxified (or unproxified if $reverse) command object record,
#   or undef if unchanged.
# Proxifying the app value is tricky, since it requires the value of tcUrl to
#   get the host and port.  Save the original tcUrl, then proxify app at the
#   end, inserting it into @out.  Hacky.
sub proxify_RTMP_command_AMF0 {
    my($in, $reverse)= @_ ;
    my(@out, $len, $segstart, $tcUrl_orig, $appvalpos) ;

    # Proxify connect command, and nothing else.
    return unless $$in=~ /\G\x02\0\x07connect\0\x3f\xf0\0\0\0\0\0\0\x03/gc ;

    while ($$in=~ /G(..)/gcs && ($len= unpack('n', $1))) {
	my $name= get_next_substring($in, $len) ;
	# would normally UTF-decode name, but we're only worried about ASCII values
	if ($name=~ /^(?:app|swfUrl|tcUrl|pageUrl)$/) {
	    push(@out, substr($in, $segstart, pos($$in)-$segstart)) ;
	    $$in=~ /\G\x02(..)/gcs or die "connect.$name has wrong AMF0 type" ;
	    my $value= get_next_substring($in, unpack('n', $1)) ;
	    $tcUrl_orig= $value  if $name eq 'tcUrl' ;
	    $value= proxify_RTMP_value($name, $value, $reverse) ;
	    $appvalpos= @out  if $name eq 'app' ;
	    push(@out, "\x02" . pack('n', length($value)) . $value) ;  # must be one element
	    $segstart= pos($$in) ;
	} else {
	    skip_value_AMF0($in) ;
	}
    }

    # After all the others, proxify app value.  Not needed when unproxifying.
    if (!$reverse and $tcUrl_orig ne '' and $appvalpos ne '') {
	my $papp= proxify_RTMP_value('app', undef, $reverse, $tcUrl_orig) ;
	splice(@out, $appvalpos, 1, "\x02" . pack('n', length($papp)) . $papp) ;
    }

    # As part of fork() hack in rtmp_proxy(), set $host and $port here.
    ($host, $port)= $tcUrl_orig=~ m#rtmp://([^/:])(?::([^/]))?#i
	if $reverse and $tcUrl_orig ne '' ;

    die "no AMF0 object end marker" unless $$in=~ /\G\x09$/ ;

    return unless @out ;     # i.e. command is unchanged
    push(@out, substr($in, $segstart)) ;
    return join('', @out) ;
}


# Returns the proxified or unproxified if $reverse) command object record,
#   or undef if unchanged.
# jsm-- this is mostly complete, but don't fully understand the AMF3 object
#   format.  Should compare with actual AMF3 examples.
sub proxify_RTMP_command_AMF3 {
    my($in, $reverse)= @_ ;
    my(@out, $segstart, @srefs, $tcUrl_orig, $appvalpos) ;

    # Proxify connect command, and nothing else.
    # jsm-- what if non-canonical U29 values are used?  Or string reference?
    if ($$in=~ /\G\x06\x47connect\x04\x01\x0a([\x60-\x6f\xe0-\xef])/gc) {
	my($class_name, $byte1, $name, $value, $flag, $u28) ;
	$byte1= ord($1) ;

	# Traits
	# These apparently include a regular array of sealed trait member
	#   names as well as an associative array of dynamic members.  Store
	#   it all in one hash, like the Array type.
	# jsm-- what is the difference between an object and a set of traits?
	my $is_dynamic= ($byte1 & 0x08)!=0 ;
	my $tcount= get_Uxx($in, 4, $byte1) ;
	for (1..$tcount) {
	    ($flag, $u28)= get_flag_U28($in) ;
	    pos($$in)+= $u28  if $flag ;    # skip string if it's not a reference
	    # jsm-- could sealed traits hold values we want to proxify?
	}
	skip_value_AMF3($in) for 1..$tcount ;
	if ($is_dynamic) {
	    do {
		($flag, $u28)= get_flag_U28($in) ;
		$name= $flag  ? get_next_substring($in, $u28)  : $srefs[$u28] ;
		if ($name=~ /^(?:app|swfUrl|tcUrl|pageUrl)$/) {
		    $$in=~ /\G\x06/  or die "connect.$name has wrong AMF3 type" ;
		    push(@out, substr($in, $segstart, pos($$in)-$segstart)) ;
		    ($flag, $u28)= get_flag_U28($in) ;
		    $value= $flag  ? get_next_substring($in, $u28)  : $srefs[$u28] ;
		    $tcUrl_orig= $value  if $name eq 'tcUrl' ;
		    $value= proxify_RTMP_value($name, $value, $reverse) ;
		    $appvalpos= @out  if $name eq 'app' ;
		    push(@out, U28(length($value)) . $value) ;  # must be one element
		    $segstart= pos($$in) ;
		} else {
		    skip_value_AMF3($in) ;
		}
	    } until $name eq '' ;
	}

	# After all the others, proxify app value.  Not needed when unproxifying.
	if (!$reverse) {
	    my $papp= proxify_RTMP_value('app', undef, $reverse, $tcUrl_orig) ;
	    splice(@out, $appvalpos, 1, U28(length($papp)) . $papp) ;
	}

	return unless @out ;     # i.e. command is unchanged
	push(@out, substr($in, $segstart)) ;
	return join('', @out) ;
    } else {
	return ;
    }
}



# Proxify (or unproxify, if $reverse) a value in an RTMP "connect" command object.
# The format for a proxified "rtmp://host:port/app/instance" is hereby
#   "rtmp://proxy_host:proxy_port/host%3aport%2fapp/instance" .
# The $tcUrl_orig parameter is part of a hack to proxify app .
sub proxify_RTMP_value {
    my($name, $value, $reverse, $tcUrl_orig)= @_ ;
    if ($reverse) {
	if ($name eq 'app') {
	    $value=~ s/%(..)/chr(hex($1))/ge ;
	    $value=~ m#^[^/]*/(.*)#s ;
	    return $1 ;
	} elsif ($name eq 'swfUrl') {
	    $value=~ s#^\Q$THIS_SCRIPT_URL/[^/]*/## ;   # jsm-- doesn't work with @PROXY_GROUP
	    return wrap_proxy_decode($value) ;
	} elsif ($name eq 'tcUrl') {
	    my($app, $instance)= $value=~ m#^rtmp://[^/]*/([^/]*)/(.*)#is ;
	    $app=~ s/%(..)/chr(hex($1))/ge ;
	    return "rtmp://$app/$instance" ;
	} elsif ($name eq 'pageUrl') {
	    $value=~ s#^\Q$THIS_SCRIPT_URL/[^/]*/## ;   # jsm-- doesn't work with @PROXY_GROUP
	    return wrap_proxy_decode($value) ;
	}
    } else {
	if ($name eq 'app') {
	    return $value unless $tcUrl_orig ;   # skip proxifying until later-- part of hack
	    my($papp)= $tcUrl_orig=~ m#rtmp://([^/]*/[^/]*)/#i ;
	    die "invalid tcUrl value '$value' (doesn't support http:// URLs yet)" unless defined $papp ;
	    $papp=~ s/([^\w.-])/ '%' . sprintf('%02x',ord($1)) /ge ;
	    return $papp ;
	} elsif ($name eq 'swfUrl') {
	    return full_url($value) ;
	} elsif ($name eq 'tcUrl') {
	    my($papp, $instance)= $value=~ m#^rtmp://([^/]*/[^/]*)/(.*)#is ;
	    die "invalid tcUrl value '$value' (doesn't support http:// URLs yet)" unless defined $papp ;
	    $papp=~ s/([^\w.-])/ '%' . sprintf('%02x',ord($1)) /ge ;
	    my $portst= $RTMP_SERVER_PORT==1935  ? ''  : ':'.$RTMP_SERVER_PORT ;
	    return "rtmp://$THIS_HOST$portst/$papp/$instance" ;
	} elsif ($name eq 'pageUrl') {
	    return full_url($value) ;
	}
    }
    die "proxify_RTMP_value() called for '$name'" ;
}


# Convenience function to get substr() and advance pos().
sub get_next_substring {
    my($in, $len)= @_ ;
    my $ret= substr($$in, pos($$in), $len) ;
    pos($$in)+= $len ;
    return $ret ;
}


# Get a U29 value from $$in.  U29 values are 1-4 bytes, have first bit set on
#   all bytes but the last, and each byte contributes 7 bits to the value,
#   except the possible fourth byte which contributes all 8 bits.
sub get_U29 {
    my($in)= @_ ;
    $$in=~ /\G([\x80-\xff]{0,3})(.)/gcs ;
    return ord($2) unless $1 ;            # shortcut for most common case
    my($last, @in)= ($2, split(//, $1)) ;
    my $ret= 0 ;
    $ret= ($ret<<7) + (ord($_)&0x7f) foreach @in ;
    return +($ret<<8) + ord($last) ;
}


# Like get_U29, but skip the first $skip_bits of the first byte.
# Include optional leading byte $byte1, if it's been read.
sub get_Uxx {
    my($in, $skip_bits, $byte1)= @_ ;

    $$in=~ /\G(.)/gcs, $byte1= ord($1)  unless defined $byte1 ;
    my $ret= $byte1 & ((1<<(7-$skip_bits))-1) ;
    return $ret unless $byte1 & 0x80 ;
    $$in=~ /\G([\x80-\xff]{0,2})(.)/gcs ;
    my($last, @in)= ($2, split(//, $1)) ;
    $ret= 0 ;
    $ret= ($ret<<7) + (ord($_)&0x7f) foreach @in ;
    return +($ret<<8) + ord($last) ;
}


# Get a U29 value from $$in, and split it into a 1-bit flag in front followed
#   by a U28.  Returns (flag, U28).
sub get_flag_U28 {
    my($in)= @_ ;
    $$in=~ /\G([\x80-\xff]{0,3})(.)/gcs ;
    return (ord($2) & 0x40, ord($2) & 0x3f)  unless $1 ;   # most common case
    my($last, @in)= (ord($2), map {ord} split(//, $1)) ;
    my($flag, $ret)= ($in[0]&0x40, $in[0]&0x3f) ;
    shift(@in) ;
    $ret= ($ret<<7) + ($_&0x7f) foreach @in ;
    return ($flag, ($ret<<8) + $last) ;
}


sub U29 {
    my($value)= @_ ;
    return chr($value)
	if $value <= 0x7f ;
    return chr(($value>>7) | 0x80) . chr($value & 0x7f)
	if $value <= 0x3fff ;
    return chr(($value>>14) | 0x80) . chr((($value>>7) & 0x7f) | 0x80)
	   . chr($value & 0x7f)
	if $value <= 0x1fffff ;
    return chr(($value>>22) | 0x80) . chr((($value>>15) & 0x7f) | 0x80)
	   . chr((($value>>8) & 0x7f) | 0x80) . chr($value & 0xff) ;
}

# This assumes a 1st bit of 1 (e.g. indicating a string literal, not a reference).
sub U28 {
    my($value)= @_ ;
    return chr($value | 0x40)
	if $value <= 0x3f ;
    return chr(($value>>7) | 0xc0) . chr($value & 0x7f)
	if $value <= 0x1fff ;
    return chr(($value>>14) | 0xc0) . chr((($value>>7) & 0x7f) | 0x80)
	   . chr($value & 0x7f)
	if $value <= 0xfffff ;
    return chr(($value>>22) | 0xc0) . chr((($value>>15) & 0x7f) | 0x80)
	   . chr((($value>>8) & 0x7f) | 0x80) . chr($value & 0xff) ;
}



# Skip past an AMF0 value in $in.  No return value.
sub skip_value_AMF0 {
    my($in)= @_ ;

    $$in=~ /\G(.)/gcs ;
    my $marker= ord($1) ;

    # Number
    if ($marker==0) {
	pos($$in)+= 8 ;

    # String
    } elsif ($marker==2) {
	$$in=~ /\G(..)/gcs ;
	pos($$in)+= unpack('n', $1) ;

    # Object
    } elsif ($marker==3) {
	while ($$in=~ /\G(..)/gcs) {
	    pos($$in)+= unpack('n', $1) ;
	    skip_value_AMF0($in) ;
	}
	die "no AMF0 object end marker" unless $$in=~ /\G\x09/gc ;

    # Reference
    } elsif ($marker==7) {
	pos($$in)+= 2 ;

    # ECMA array
    } elsif ($marker==8) {
	pos($$in)+= 4 ;
	while ($$in=~ /\G(..)/gcs) {
	    pos($$in)+= unpack('n', $1) ;
	    skip_value_AMF0($in) ;
	}
	die "no AMF0 object end marker" unless $$in=~ /\G\x09/gc ;

    # Object end
    # These should only happen as part of another value, so ignore here.
    #} elsif ($marker==9) {

    # Strict Array
    } elsif ($marker==0x0a) {
	$$in=~ /\G(....)/gcs ;
	skip_value_AMF0($in) for 1..unpack('N', $1) ;

    # Date
    } elsif ($marker==0x0b) {
	pos($$in)+= 10 ;

    # Long String
    } elsif ($marker==0x0c) {
	$$in=~ /\G(....)/gcs ;
	pos($$in)+= unpack('N', $1) ;

    # XML document
    } elsif ($marker==0x0f) {
	$$in=~ /\G(....)/gcs ;
	pos($$in)+= unpack('N', $1) ;

    # Typed object
    } elsif ($marker==0x10) {
	$$in=~ /\G(..)/gcs ;
	pos($$in)+= unpack('n', $1) ;
	while ($$in=~ /\G(..)/gcs) {
	    pos($$in)+= unpack('n', $1) ;
	    skip_value_AMF0($in) ;
	}
	die "no AMF0 object end marker" unless $$in=~ /\G\x09/gc ;

    # AVMplus object, i.e. use AMF3
    } elsif ($marker==0x11) {
	skip_value_AMF3($in) ;

    # all other types are either 0-length or unsupported.

    } elsif ($marker>0x11) {
	die "unrecognized AVM0 marker: [$marker]" ;
    }
}


# Skip past an AMF3 value in $in.  No return value.
sub skip_value_AMF3 {
    my($in)= @_ ;
    my($flag, $u28) ;

    $$in=~ /\G(.)/gcs ;
    my $marker= ord($1) ;

    # Integer
    if ($marker==4) {
	$$in=~ /\G([\x80-\xff]{0,3})(.)/gcs ;

    # Double
    } elsif ($marker==5) {
	pos($$in)+= 8 ;

    # String
    } elsif ($marker==6) {
	($flag, $u28)= get_flag_U28($in) ;
	pos($$in)+= $u28 if $flag ;

    # XMLDocument
    } elsif ($marker==7) {
	($flag, $u28)= get_flag_U28($in) ;
	pos($$in)+= $u28 if $flag ;

    # Date
    } elsif ($marker==8) {
	($flag)= get_flag_U28($in) ;
	pos($$in)+= 8 if $flag ;

    # Array
    } elsif ($marker==9) {
	($flag, $u28)= get_flag_U28($in) ;
	if ($flag) {
	    # First, skip associative array.
	    while (!$$in=~ /\G\x01/gc) {
		($flag, $u28)= get_flag_U28($in) ;
		pos($$in)+= $u28 if $flag ;
		skip_value_AMF3($in) ;
	    }
	    # Then, skip normal array, sized by first $u28.
	    skip_value_AMF3($in) for 1..$u28 ;
	}

    # Object
    } elsif ($marker==0x0a) {
	$$in=~ /\G(.)/gcs ;
	my $byte1= ord($1) ;
	pos($$in)-- ;

	# Object reference
	if (($byte1 & 0x40)==0) {
	    $$in=~ /\G([\x80-\xff]{0,3})(.)/gcs ;
	# Trait reference
	} elsif (($byte1 & 0x20)==0) {
	    $$in=~ /\G([\x80-\xff]{0,3})(.)/gcs ;
	# Traits
	# These apparently include a regular array of sealed trait member
	#   names as well as an associative array of dynamic members.  Store
	#   it all in one hash, like the Array type.
	# jsm-- what is the difference between an object and a set of traits?
	} elsif (($byte1 & 0x10)==0) {
	    my $is_dynamic= ($byte1 & 0x08)!=0 ;
	    my $tcount= get_Uxx($in, 4) ;
	    ($flag, $u28)= get_flag_U28($in) ;
	    pos($$in)+= $u28 if $flag ;
	    for (1..$tcount) {
		($flag, $u28)= get_flag_U28($in) ;
		pos($$in)+= $u28 if $flag ;
	    }
	    skip_value_AMF3($in) for 1..$tcount ;
	    if ($is_dynamic) {
		do {
		    ($flag, $u28)= get_flag_U28($in) ;
		    pos($$in)+= $u28 if $flag ;
		    skip_value_AMF3($in) unless $u28==0 ;
		} until $u28==0 ;   # jsm-- is this right?  Spec says 0x01....
	    }

	# Externalizable trait (not supported; handled by client/server agreement)
	} elsif (($byte1 & 0x10)!=0) {
	    die "externalizable trait not supported" ;
	}


    # XML
    } elsif ($marker==0x0b) {
	my($flag, $u28)= get_flag_U28($in) ;
	pos($$in)+= $u28 if $flag ;

    # ByteArray
    } elsif ($marker==0x0c) {
	my($flag, $u28)= get_flag_U28($in) ;
	pos($$in)+= $u28 if $flag ;

    # all other types are either 0-length or unsupported.

    } elsif ($marker>0x11) {
	die "unrecognized AVM0 marker: [$marker]" ;
    }
}



# Fork off and start a generic listening TCP server, one that in turn forks
#   off client connections.
# Invokes &$coderef($NEW_SOCKET_HANDLE) in each child process, after accept().
# Takes the listening socket, the lock filehandle, a code reference, a timeout,
#   and any additional arguments to the code reference as params.  The timeout,
#   in seconds, applies to the daemon process; 0 means no timeout.
# Returns daemon PID on success.
# Be very careful to get rid of all instances that are started!
# This routine used to include create_server_lock() and new_server_socket(),
#   but the port number returned from new_server_socket() is needed before
#   calling this.
# This routine is liberal about die'ing.  Consider using eval{} to trap those.
# This is actually much more complicated than it needs to be for the HTTP
#   server, when run from the command line.  We don't really need to
#   double-fork (and more) in that case, since the parent process is almost
#   immediately exiting.
# jsm-- should we maintain a list of running daemons?
sub spawn_generic_server {
    my($LISTEN, $LOCK_FH, $coderef, $timeout, @args)= @_ ;

    my $new_pid= double_fork_daemon($LOCK_FH, $LISTEN) ;
    return $new_pid  if $new_pid ;

    my $port= (unpack_sockaddr_in(getsockname($LISTEN)))[0] ;   # get the port bound to

    # Record port and PID in lockfile.
    select((select($LOCK_FH), $|=1)[0]) ;   # make $LOCK_FH autoflush output
    seek($LOCK_FH, 0, 0) ;
    print $LOCK_FH "$port,$$\n" ;

    # Clear permissions mask, for easier file-handling.
    umask 0 ;

    $SIG{CHLD} = \&REAPER;

    # Daemon dies if not used for $timeout seconds.
    $SIG{ALRM}= sub {exit} ;
    eval { alarm($timeout) } ;   # use eval{} to avoid failing where alarm() is missing

    # jsm-- should allow stopping process via x-proxy://admin/stop-daemon ?
    my $paddr ;
    while (1) {
	my($SS) ;
	$paddr= accept($SS, $LISTEN) ;
	next if !$paddr and $!==EINTR ;
	die "failed accept: $!"  unless $paddr ;

	# Restart timer upon each incoming connection.
	eval { alarm($timeout) } ;   # use eval{} to avoid failing where alarm() is missing

	my $pid= fork() ;
	die "failed fork: $!"  unless defined($pid) ;
	close($SS), next if $pid ;   # parent daemon process

	# After here is the per-connection process.

	# Processes handling connections don't have a timeout.
	eval { alarm(0) } ;   # use eval{} to avoid failing where alarm() is missing

	# They also shouldn't hold the lock.
	close($LOCK_FH) ;

	exit(&$coderef($SS, $port, @args)) ;
    }


    # Kill zombie children spawned by the daemon's fork.
    sub REAPER {
	local $! ;
	1 while waitpid(-1, WNOHANG)>0 and WIFEXITED($?) ;
	$SIG{CHLD} = \&REAPER;
    }

}


# Open and lock a file, creating it if needed.
# Returns either: the lockfile handle, or (undef, port, pid) if the the file
#   is already locked (indicating that the server is already running).
# Uses lock on $lock_file to ensure one instance only.  Thus, use the same
#   $lock_file for all calls that spawn the same daemon.  $lock_file also stores
#   the port and PID of the final daemon process.
sub create_server_lock {
    my($lock_file)= @_ ;
    my($LOCK) ;

    # First, open and get lock on $lock_file, to avoid duplicates daemons.
    die "illegal lock_file name: [$lock_file]"
	if $lock_file=~ /\.\./ or $lock_file=~ m#^/# or $lock_file=~ /[^\w.-]/
	  or $lock_file eq '' ;
    -d $PROXY_DIR or mkdir($PROXY_DIR, 0755) or die "mkdir [$PROXY_DIR]: $!" ;
    open($LOCK, (-s "$PROXY_DIR/$lock_file"  ? '+<'  : '+>'), "$PROXY_DIR/$lock_file") || die "open: $!" ;
    if (!flock($LOCK, LOCK_EX|LOCK_NB)) {    # daemon already started
	my($port, $pid)= ((scalar <$LOCK>)=~ /(\d+)/g) ;
	close($LOCK) ;
	return (undef, $port, $pid) ;
    }

    return ($LOCK) ;
}


# Opens a generic server socket and starts listening.  Use $port if possible,
#   else use any available port.  Returns (listening socket, port used).
# This routine is liberal about die'ing.  Consider using eval{} to trap those,
#   or returning undef.
sub new_server_socket {
    my($port)= @_ ;

    # Create and listen on server socket.
    my($LISTEN) ;
    socket($LISTEN, AF_INET, SOCK_STREAM, (getprotobyname('tcp'))[2]) or die "socket: $!" ;
    setsockopt($LISTEN, SOL_SOCKET, SO_REUSEADDR, 1) or die "setsockopt: $!" ;
    bind($LISTEN, sockaddr_in($port, INADDR_ANY))
	or bind($LISTEN, sockaddr_in(0, INADDR_ANY)) or die "bind: $!" ;
    $port= (unpack_sockaddr_in(getsockname($LISTEN)))[0] ;   # get the port bound to
    listen($LISTEN, SOMAXCONN) or die "listen: $!" ;

    return ($LISTEN, $port) ;
}


# Double-forks a daemon process.  Returns the resulting PID in the parent,
#   or 0 in the resulting grandchild daemon.
sub double_fork_daemon {
    my($LOCK_FH, $LISTEN)= @_ ;

    # Open pipe to communicate PID back to caller.
    my($PIPE_P, $PIPE_C) ;
    pipe($PIPE_P, $PIPE_C) ;

    # First fork...
    my $pid= fork() ; 
    die "fork: $!"  unless defined($pid) ;

    # First parent process returns.
    if ($pid) {
	close($PIPE_C) ;
	close($LISTEN) ;
	close($LOCK_FH) if $LOCK_FH ;
	my $finalpid= <$PIPE_P> ;
	close($PIPE_P) ;
	return $finalpid ;
    }

    # Child process continues.

    close($PIPE_P) ;

    # Close filehandles in child process.
    close(S) ;         # in case it's open from somewhere

    # This is required for a daemon, to disconnect from controlling terminal
    #   and current process group.
    setsid() || die "setsid: $!"  unless $^O=~ /win/i ;

    # Fork again to guarantee no controlling terminal.
    $pid= fork() ; 
    die "fork: $!"  unless defined($pid) ;

    # Send the PID to the parent process.
    print $PIPE_C "$pid\n" if $pid;
    close($PIPE_C) ;

    # Exit second parent process.
    exit(0) if $pid ;

    # Second child process continues.  This is the daemon process.

    return 0 ;
}



#--------------------------------------------------------------------------

#
# <scheme>_fix: modify response as appropriate for given protocol (scheme).
#

# http_fix: modify headers as needed, including cookie support.
# Note that headers have already been unfolded, when they were read in.
# Some HTTP headers are defined as comma-separated lists of values, and they
#   should be split before being processed.  According to the HTTP spec in
#   RFC 2616, such headers are:
#     Accept|Accept-Charset|Accept-Encoding|Accept-Language|Accept-Ranges|
#     Allow|Cache-Control|Connection|Content-Encoding|Content-Language|
#     If-Match|If-None-Match|Pragma|Public|Transfer-Encoding|Upgrade|Vary|
#     Via|Warning|WWW-Authenticate
#   As it turns out, none need to be handled in new_header_value().  Thus, we
#   don't need to split any standard headers before processing.  See section
#   4.2 of RFC 2616, plus the header definitions, for more info.

# Conceivably, Via: and Warning: could be exceptions to this, since they
#   do contain hostnames.  But a) these are primarily for diagnostic info and
#   not used to connect to those hosts, and b) we couldn't distinguish the
#   hostnames from pseudonyms anyway.
# Unfortunately, the non-standard Link: and URI: headers may be lists, and
#   we *do* have to process them.  Because of their unusual format and rarity,
#   these are handled as lists directly in new_header_value().
sub http_fix {
    my($name, $value, $new_value) ;
    my(@headers)= $headers=~ /^([^\012]*\012?)/mg ;  # split into lines

    foreach (@headers) {
	next unless ($name, $value)= /^([\w.-]+):\s*([^\015\012]*)/ ;
	$new_value= &new_header_value($name, $value) ;
	$_= defined($new_value)
	    ? "$name: $new_value\015\012"
	    : '' ;
    }

    $headers= join('', @headers) ;
}


# Returns the value of an updated header, e.g. with URLs transformed to point
#   back through this proxy.  Returns undef if the header should be removed.
# This is used to translate both real headers and <meta http-equiv> headers.
# Special case for URI: and Link: -- these headers can be lists of values
#   (see the HTTP spec, and comments above in http_fix()).  Thus, we must
#   process these headers as lists, i.e. transform each URL in the header.
sub new_header_value {
    my($name, $value)= @_ ;
    $name= lc($name) ;

    # sanity check
    return undef if $name eq '' ;

    # These headers consist simply of a URL.
    # Note that all these are absolute URIs, except possibly Content-Location:,
    #   which may be relative to Content-Base or the request URI-- notably, NOT
    #   relative to anything in the content, like a <base> tag.
    return &full_url($value)
	if    $name eq 'content-base'
	   || $name eq 'content-location' ;

    # Location: header should carry forward the expected type, since some sites
    #   (e.g.. hotmail) may 302 forward to another URL and use the wrong
    #   Content-Type:, and that retrieved resource may still be treated by the
    #   browser as of the expected type.  Here we just carry forward the entire
    #   flag segment.
    if ($name eq 'location') {
	local($url_start)= $script_url . '/' . $packed_flags . '/' ;
	return &full_url($value) ;
    }


    # Modify cookies to point back through the script, or they won't work.
    # If they're banned from this server, or if $NO_COOKIE_WITH_IMAGE or
    #   $e_filter_ads is set and the current resource isn't text, then filter
    #   them all out.
    # We guess whether the current resource is text or not by using both
    #   the Content-Type: response header and the Accept: header in the
    #   original request.  Content-Type: can be something text, something
    #   non-text, or it can be absent; Accept: can either accept something
    #   text or not.  Our test here is that the resource is non-text either
    #   if Accept: accepts no text, or if Content-Type: indicates non-text.
    #   Put another way, it's text if Accept: can accept text, and
    #   Content-Type: is either a text type, or is absent.
    # This test handles some cases that failed with earlier simpler tests.
    #   One site had a cookie in a 302 response for a text page that didn't
    #   include a Content-Type: header.  Another site was sneakier--
    #   http://zdnet.com returns an erroneous response that surgically
    #   bypassed an earlier text/no-text test here:  a redirection
    #   response to an image contains cookies along with a meaningless
    #   "Content-Type: text/plain" header.  They only do this on images that
    #   look like Web bugs.  So basically that means we can't trust
    #   Content-Type: alone, because a malicious server has full control over
    #   that header, whereas the Accept: header comes from the client.
    if ($name eq 'set-cookie') {
	return undef if $cookies_are_banned_here ;
	if ($NO_COOKIE_WITH_IMAGE || $e_filter_ads) {
	    return undef
		if ($headers=~ m#^Content-Type:\s*(\S*)#mi  &&  $1!~ m#^text/#i)
		   || ! grep(m#^(text|\*)/#i, split(/\s*,\s*/, $env_accept)) ;
	}

	return &cookie_to_client($value, $path, $host) ;
    }


    # Extract $default_style_type as needed.
    # Strictly speaking, a MIME type is "token/token", where token is
    #    ([^\x00-\x20\x7f-\xff()<>@,;:\\"/[\]?=]+)   (RFCs 1521 and 822),
    #   but this below covers all existing and likely future MIME types.
    if ($name eq 'content-style-type') {
	$default_style_type= lc($1)  if $value=~ m#^\s*([/\w.+\$-]+)# ;
	return $value ;
    }


    # Extract $default_script_type as needed.
    # Same deal about "token/token" as above.
    if ($name eq 'content-script-type') {
	$default_script_type= lc($1)  if $value=~ m#^\s*([/\w.+\$-]+)# ;
	return $value ;
    }


    # Handle P3P: header.  P3P info may also exist in a <link> tag (or
    #   conceivably a Link: header), but those are already handled correctly
    #   where <link> tags (or Link: headers) are handled.
    if ($name eq 'p3p') {
	$value=~ s/\bpolicyref\s*=\s*['"]?([^'"\s]*)['"]?/
		   'policyref="' . &full_url($1) . '"' /gie ;
	return $value ;
    }


    # And the non-standard Refresh: header... any others?
    $value=~ s/(;\s*URL\s*=)\s*((?>['"]?))(\S*)\2/ $1 . &full_url($3) /ie,   return $value
	if $name eq 'refresh' ;

    # The deprecated URI: header may contain several URI's, inside <> brackets.
    $value=~ s/<(\s*[^>\015\012]*)>/ '<'.&full_url($1).'>' /gie, return $value
	if $name eq 'uri' ;


    # The non-standard Link: header is a little problematic.  It's described
    #   in the HTTP 1.1 spec, section 19.6.2.4, but it is not standard.  Among
    #   other things, it can be used to link to style sheets, but the mechanism
    #   for indicating the style sheet type (=language, which could be a script
    #   MIME type) is not defined.
    # The HTML 4.0 spec (section 14.6) gives a little more detail regarding
    #   its use of the Link: header, but is still ambiguous-- e.g. their
    #   examples don't specify the type, though elsewhere it's implied that's
    #   required.
    # Generally speaking, we handle this like a <link> tag.  For notes about
    #   this block, see the block above that handles <link> tags.  For a
    #   description of the unusual format of this header, see the HTTP spec.
    # Note that this may be a list of values, and all URIs in it must be
    #   handled.  This gets a little messy, because we split on commas, but
    #   don't split on commas that are inside <> brackets, because that's
    #   the URL.
    if ($name eq 'link') {
	my($v, @new_values) ;

	my(@values)= $value=~ /(<[^>]*>[^,]*)/g ;
	foreach $v (@values) {
	    my($type)= $v=~ m#[^\w.\/?&-]type\s*=\s*["']?\s*([/\w.+\$-]+)#i ;
	    $type= lc($type) ;

	    if ($type eq '') {
		my($rel) ;
		$rel= $+
		    if $v=~ /[^\w.\/?&-]rel\s*=\s*("([^"]*)"|'([^']*)'|([^'"][^\s]*))/i ;
		$type= 'text/css' if $rel=~ /\bstylesheet\b/i ;
	    }

	    return undef
		if $scripts_are_banned_here && $type=~ /^$SCRIPT_TYPE_REGEX$/io ;

	    local($url_start)= $url_start ;
	    if ($type ne '') {
		$url_start= $script_url . '/' .
		    &pack_flags($e_remove_cookies, $e_remove_scripts, $e_filter_ads,
				$e_hide_referer, $e_insert_entry_form,
				$is_in_frame, $type)
			. '/' ;
	    }

	    $v=~ s/<(\s*[^>\015\012]*)>/ '<' . &full_url($1) . '>' /gie ;
	    push(@new_values, $v) ;
	}

	return join(', ', @new_values) ;
    }



    # For all non-special headers, return $value
    return $value ;

}


#--------------------------------------------------------------------------
#    Special admin routines, when called via the scheme type "x-proxy://"
#--------------------------------------------------------------------------

#--------------------------------------------------------------------------
#
#   I took the liberty of creating a general mechanism to let this proxy do
#   whatever tricks it needs to do, via the magic URL scheme "x-proxy://".
#   It was required to support HTTP Basic Authentication, and it's useful
#   for other things too.  The mechanism uses a heirarchical URL space: a
#   function family is in the normal "hostname" location, then the functions
#   and subfunctions are where the path segments would be.  A query string
#   is allowed on the end.
#
#   Don't add functions to this that may compromise security, since anyone
#   can request a URL beginning with x-proxy://.  For that matter, malicious
#   Web pages can automatically invoke these URLs, which could be annoying
#   if e.g. they clear your cookies without warning or other acts.
#
#   Which URLs map to which functions should really be documented here.  So,
#
#     //auth/make_auth_cookie
#         receives the authorization form data, sends a formatted auth
#         cookie to the user, and redirects the user to the desired URL.
#
#     //start
#         initiates a browsing session.
#
#     //cookies/clear
#         clears all of a user's cookies.
#
#     //cookies/manage
#         present the user with a page to manage her/his cookies
#
#     //cookies/update
#         process whatever actions are requested from the //cookies/manage
#         page (currently only deletion of cookies).
#
#     //cookies/set-cookie
#         set the cookie from the query string
#
#     //frames/topframe
#         returns the special top frame with the entry form and/or the
#         other insertion.
#
#     //frames/framethis
#         given a URL, returns a page that frames that URL in the lower
#         frame with the top frame above (not currently used).
#
#     //scripts/jslib
#         returns the JavaScript library used when rewriting JavaScript.
#         Normally, this can be cached for efficiency.
#
#--------------------------------------------------------------------------

# A general-purpose routine to handle all x-proxy requests.
# This is expected to exit when completed, so make sure any called routines
#   exit if needed.  (By "exit", I mean "die 'exiting'".)
sub xproxy {
    my($URL)= @_ ;
    $URL=~ s/^x-proxy://i ;

    # $qs will contain the query string in $URL, whether it was encoded with
    #   the URL or came from QUERY_STRING.
    my($family, $function, $qs)=  $URL=~ m#^//(\w+)(/?[^?]*)\??(.*)#i ;

    if ($family eq 'auth') {

	# For //auth/make_auth_cookie, return an auth cookie and redirect user
	#   to the desired URL.  The URL is already encoded in $in{'l'}.
	if ($function eq '/make_auth_cookie') {
	    my(%in)= &getformvars() ; # must use () or will pass current @_!
	    my($location)= $url_start . $in{'l'} ;  # was already encoded
	    my($cookie)= &auth_cookie(@in{'u', 'p', 'r', 's'}) ;

	    &redirect_to($location, "Set-Cookie: $cookie\015\012") ;
	}


    } elsif ($family eq 'start') {
	&startproxy ;


    } elsif ($family eq 'cookies') {

	# Store in the database a cookie sent encoded in the query string.
	if ($function eq 'set-cookie') {
	    # This does checks, then stores cookie in database.
	    &cookie_to_client(cookie_decode($qs), $path, $host)  if $USE_DB_FOR_COOKIES ;
	    print $STDOUT "$HTTP_1_X 204 No Content\015\012",
			  "Cache-Control: no-cache\015\012",
			  "Pragma: no-cache\015\012\015\012" ;
	    die 'exiting' ;


	# If pages could link to x-proxy:// URLs directly, this would be a
	#   security hole in that malicious pages could clear or update one's
	#   cookies.  But full_url() prevents that.  If that changes, then we
	#   should consider requiring POST in /cookie/clear and /cookie/update
	#   to minimize this risk.
	} elsif ($function eq '/clear') {
	    my($location)=
		$url_start . &wrap_proxy_encode('x-proxy://cookies/manage') ;
	    $location.= '?' . $qs    if $qs ne '' ;

	    &redirect_to($location, &cookie_clearer($ENV{'HTTP_COOKIE'})) ;


	} elsif ($function eq '/manage') {
	    &manage_cookies($qs) ;


	# For //cookies/update, clear selected cookies and go to manage screen.
	} elsif ($function eq '/update') {
	    my(%in)= &getformvars() ; # must use () or will pass current @_!
	    my($location)=
		$url_start . &wrap_proxy_encode('x-proxy://cookies/manage') ;

	    # Add encoded "from" parameter to URL if available.
	    if ($in{'from'} ne '') {
		my($from_param)= $in{'from'} ;
		$from_param=~ s/([^\w.-])/ '%' . sprintf('%02x',ord($1)) /ge ;
		$location.=  '?from=' . $from_param ;
	    }

	    # "delete=" input fields are in form &base64(&cookie_encode($name)).
	    my(@cookies_to_delete)= map {cookie_decode(&unbase64($_))} split(/\0/, $in{'delete'}) ;

	    if ($USE_DB_FOR_COOKIES) {
		&delete_cookies_from_db(@cookies_to_delete) ;
		&redirect_to($location) ;
	    } else {
		&redirect_to($location, &cookie_clearer(@cookies_to_delete)) ;
	    }
	}


    } elsif ($family eq 'frames') {
	my(%in)= &getformvars($qs) ;

	# Send the top proxy frame when a framed page is reframed.
	if ($function eq '/topframe') {
	    &return_top_frame($in{'URL'}) ;

	# Not currently used
	} elsif ($function eq '/framethis') {
	    &return_frame_doc($in{'URL'}, &HTMLescape(&wrap_proxy_decode($in{'URL'}))) ;
	}


    } elsif ($family eq 'scripts') {

	# Return the library needed for JavaScript rewriting.  Normally, this
	#   can be cached.
	if ($function eq '/jslib') {
	    &return_jslib ;
	}


    }


warn "no such function as x-proxy://$family$function\n" ;
    &HTMLdie("Sorry, no such function as //". &HTMLescape("$family$function."),
	     '', '404 Not Found') ;

}


sub return_flash_vars {
    my($s)= @_ ;
    my($len)= length($s) ;
    my($date_header)= &rfc1123_date($now, 0) ;
warn "in return_flash_vars($s)" ;                   # this indicates success...  :?

    print $STDOUT <<EOF . $s ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: application/x-www-form-urlencoded
Content-Length: $len

EOF

    die "exiting" ;
}


#--------------------------------------------------------------------------
#    Support routines for x-proxy
#--------------------------------------------------------------------------

# Initiate a browsing session. Formerly in the separate program startproxy.cgi.
sub startproxy {
    my(%in)= &getformvars() ;  # must use () or will pass current @_!


    # Decode URL if it was encoded before transmission.
    # Chrome chokes on some chars here, and other browsers choke on others.  :P
    my $encode_prefix= $ENV{HTTP_USER_AGENT}=~ /Chrome|Safari/  ? "\x7f"  : "\x01" ;
    $in{'URL'}= &wrap_proxy_decode($in{'URL'})
	if $ENCODE_URL_INPUT && $in{'URL'}=~ s/^$encode_prefix+// ;

    $in{'URL'}=~ s/^\s+|\s+$//g ;    # strip leading or trailing spaces

    &show_start_form('Enter the URL you wish to visit in the box below.')
	if $in{'URL'} eq '' or $in{'URL'}=~ /[\0\x0d\x0a]/ ;   # protect against HTTP header injection

    # Handle (badly) the special case of "mailto:" URLs, which don't have "://".
    &unsupported_warning($in{URL}) if $in{URL}=~ /^mailto:/i ;

    # Parse input URI into components, using a regex similar to this one in
    #   RFC 2396:  ^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?
    # Here, $query and $fragment include their initial "?" and "#"  chars,
    #   and $scheme is undefined if there's no "://" .
    my($scheme, $authority, $path, $query, $fragment)=
	$in{URL}=~ m{^(?:([^:/?#]+)://)?([^/?#]*)([^?#]*)(\?[^#]*)?(#.*)?$} ;
    $scheme= lc($scheme) ;
    $path= '/' if $path eq '' ;

    # Parse $authority into username/password, hostname, and port-string.
    my($auth, $host, $portst)= $authority=~ /^([^@]*@)?([^:@]*)(:[^@]*)?$/ ;

    &show_start_form('The URL you entered has an invalid host name.', $in{URL})
	if !defined($host) ;

    $host= lc($host) ;   # must be after testing defined().

    &show_start_form('The URL must contain a valid host name.', $in{URL})
	if $host eq '' ;

    # Scheme defaults to FTP if host begins with "ftp.", else to HTTP.
    $scheme= ($host=~ /^ftp\./i)  ? 'ftp'  : 'http'   if $scheme eq '' ;

    &show_start_form('Sorry, only HTTP and FTP are currently supported.', $in{URL})
	unless $scheme=~ /^(http|https|ftp|x-proxy)$/ ;

    # Convert integer hostnames like 3467251275 to a.b.c.d format.
    # This is for big-endian; reverse the list for little-endian.
    $host= join('.', $host>>24 & 255, $host>>16 & 255, $host>>8 & 255, $host & 255)
	if $host=~ /^\d+$/ ;

    # Allow shorthand for hostnames-- if no "." is in it, then add "www"+"com"
    #   or "ftp"+"com".  Don't do it if the host already exists on the LAN.
    if ($scheme eq 'http') {
	$host= "www.$host.com"  if ($host!~ /\./) && !gethostbyname($host) ;
    } elsif ($scheme eq 'ftp') {
	# If there's username/password embedded (which you REALLY shouldn't do),
	#   then don't risk sending that to an unintended host.
	$host= "ftp.$host.com"
	    if ($auth eq '') && ($host!~ /\./) && !gethostbyname($host) ;
    }

    # Force $portst to ":" followed by digits, or ''.
    ($portst)= $portst=~ /^(:\d+)/ ;

    # Reassemble $authority after all changes are complete.
    $authority= $auth . $host . $portst ;

    # Prepend flag segment of PATH_INFO
    # This "erroneously" sets flags to "000000" when user config is not
    #   allowed, but it doesn't really affect anything.
    $url_start=~ s#[^/]*/$## ;   # remove old flag segment from $url_start
    $url_start.= &pack_flags(@in{'rc', 'rs', 'fa', 'br', 'if'}, $is_in_frame, '') . '/' ;

    &redirect_to( $url_start . &wrap_proxy_encode("$scheme://$authority$path$query") . $fragment ) ;
}



# Create the flag segment of PATH_INFO from the given flags, not including
#   slashes.  Result should be a valid path segment (i.e. alphanumeric and
#   certain punctuation OK, but no slashes or white space).
# This routine defines the structure of the flag segment.
# Note that an $expected_type of '' explicitly means that no type in particular
#   is expected, which will be the case for almost all resources.
# Note that any unrecognized MIME type (i.e. no element in %MIME_TYPE_ID)
#   is treated the same as '', i.e. element #0 -> "0" .
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_pack_flags() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   (almost) a Perl-to-JavaScript translation of this routine.
sub pack_flags {
    my($remove_cookies, $remove_scripts, $filter_ads, $hide_referer,
	  $insert_entry_form, $is_in_frame, $expected_type)= @_ ;

    my $total= !!$remove_cookies    *32
	     + !!$remove_scripts    *16
	     + !!$filter_ads        *8
	     + !!$hide_referer      *4
	     + !!$insert_entry_form *2
	     + !!$is_in_frame ;

    my $ret= chr($total).chr($MIME_TYPE_ID{lc($expected_type)}) ;
    $ret=~ tr/\x00-\x3f/0-9A-Za-z\-_/ ;

    return $ret ;
}


# The reverse of pack_flags()-- given a flag segment from PATH_INFO, break
#   out all flag info.  The return list should match the input list for
#   pack_flags().
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_unpack_flags() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   (almost) a Perl-to-JavaScript translation of this routine.
sub unpack_flags {
    my($flags)= @_ ;
    my($remove_cookies, $remove_scripts, $filter_ads, $hide_referer,
       $insert_entry_form, $is_in_frame, $expected_type) ;

    $flags=~ tr/0-9A-Za-z\-_/\x00-\x3f/ ;
    ($flags, $expected_type)= map {ord} split(//, $flags) ;

    $remove_cookies=    ($flags & 32) ? 1 : 0 ;
    $remove_scripts=    ($flags & 16) ? 1 : 0 ;
    $filter_ads=        ($flags & 8)  ? 1 : 0 ;
    $hide_referer=      ($flags & 4)  ? 1 : 0 ;
    $insert_entry_form= ($flags & 2)  ? 1 : 0 ;
    $is_in_frame=       ($flags & 1)  ? 1 : 0 ;

    # Extract expected MIME type from final one-character flag
    $expected_type= $ALL_TYPES[$expected_type] ;

    return ($remove_cookies, $remove_scripts, $filter_ads, $hide_referer,
	    $insert_entry_form, $is_in_frame, $expected_type) ;
}


#--------------------------------------------------------------------------
#    Cookie routines
#--------------------------------------------------------------------------

# As of version 1.3, cookies are now a general mechanism for sending various
#   data to the proxy.  So far that's only authentication info and actual
#   cookies, but more functions could be added.  The new scheme essentially
#   divides up the cookie name space to accommodate many categories.
# Explanation: Normally, a cookie is uniquely identified ("keyed") by the
#   domain, path, and name, but for us the domain and path will always be
#   that of the proxy script, so we need to embed all "key" information into
#   the cookie's name.  Here, the general format for a cookie's name is
#   several fields, joined by ";".  The first field is always a cookie type
#   identifier, like "AUTH" or "COOKIE", and the remaining fields vary
#   according to cookie type.  This compound string is then URL-encoded as
#   necessary (cookie names and values can't contain semicolons, commas, or
#   white space).  The cookie's value contains whatever you need to store,
#   also URL-encoded as necessary.

# A general bug in cookie routines-- ports are not considered, which may
#   matter for both AUTH and COOKIE cookies.  It only matters when two ports
#   on the same server are being used.


# Returns all info we need from cookies.  Right now, that means one composite
#   cookie with all cookies that match the domain and path (and no others!),
#   and an %auth hash to look up auth info by server and realm.  Essentially,
#   this undoes the transformation done by the cookie creation routines.
# @auth is used instead of %auth for slight speedup.
# See notes where the various cookies are created for descriptions of their
#   format; currently, that's in cookie_to_client() and auth_cookie().
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_cookie_from_client() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of part of this routine.
sub parse_cookie {
    my($cookie, $target_path, $target_server, $target_port, $target_scheme)= @_ ;
    my($name, $value, $type, $subtype, @n,
       $cname, $path, $domain, $cvalue, $secure, @matches, %pathlen,
       $realm, $server, @auth) ;

    foreach ( split(/\s*;\s*/, $cookie) ) {
	($name, $value)= split(/=/, $_, 2) ;     # $value may contain "="

	# Set $session_id and $session_id_persistent from S and S2 cookies.
	if ($USE_DB_FOR_COOKIES) {
	    $session_id= $value, next  if $name eq 'S' ;
	    $session_id_persistent= $value, next  if $name eq 'S2' ;
	}

	$name= &cookie_decode($name) ;
	$value= &cookie_decode($value) ;
	($type, @n)= split(/;/, $name) ;
	if ($type eq 'COOKIE') {
	    ($cname, $path, $domain)= @n ;
	    $domain= lc($domain) ;
	    ($cvalue, $secure)= split(/;/, $value) ;
	    next if $secure && ($target_scheme ne 'https') ;

	    # According to the cookie spec, a cookie domain equal to a "."
	    #   plus the target domain should not match, but browsers treat
	    #   it as if it does, so we do the same here.
	    if ( ($target_server=~ /\Q$domain\E$/i or (lc('.'.$target_server) eq lc($domain)) )
		 && $target_path=~ /^\Q$path\E/ )
	    {
		# Cookies are always supposed to have a name, but some servers
		#   don't follow this, and at least one browser treats it as
		#   cookie with only "value" instead of "name=value".  So,
		#   we follow that here, for these errant cookies.
		push(@matches, ($cname ne '' ? $cname.'='.$cvalue : $cvalue)) ;
		$pathlen{$matches[$#matches]}= length($path) ;
	    }
	} elsif ($type eq 'AUTH') {
	    # format of auth cookie's name is AUTH;$enc_realm;$enc_server
	    ($realm, $server)= @n ;
	    $realm=~  s/%([\da-fA-F]{2})/ pack('C', hex($1)) /ge ;
	    $server=~ s/%([\da-fA-F]{2})/ pack('C', hex($1)) /ge ;
	    my($portst)= ($target_port eq '')  ? ''  : ":$target_port" ;
	    push(@auth, $realm, $value)
		if  $server eq "$target_server$portst" ;
	}
    }

    # More specific path mappings (i.e. longer paths) should be sent first.
    $cookie= join('; ', sort { $pathlen{$b} <=> $pathlen{$a} } @matches) ;

    return $cookie, @auth ;
}


# Old notes:
#
# Cookie support:  The trick is how to send a cookie back to the client that
#   it will return for appropriate hosts.  Given that the target URL may be
#   encoded, and the client can't always tell where the target URL is, the
#   only way to do that is to get *all* the cookies from the client and send
#   along the matching ones.  If the client has a lot of cookies through the
#   proxy, this could conceivably be a problem.  Oh well, it works for the
#   limited amount I've tested.
# Here, we transform the cookie from the server into something the client
#   will always send back to us, and embed the real server/path info in the
#   name of the name-value pair, since the cookie is uniquely identified by
#   the domain, path, and name.  Upon return from the client, we split the
#   name back into its original fields.
# One way to get around *some* of the all-cookies-all-the-time problem,
#   *sometimes*, may be possible to program with the following approach:
#   First, the target URL must be "encoded" (in proxy_encode()) in a way
#   that it resembles a path.  For example, the default "://" --> "/"
#   encoding does this.  Then, let the cookies go back to the client with
#   the target paths still intact.  This would only work when the cookie
#   domain is the default, i.e. the source host.  Check other possibilities
#   carefully, too, but I think you could get it to work somehow.
# Question-- is the port supposed to be used in the domain field?
#   Everything here assumes not, which is conceivably a security risk.

# Transform one cookie into something the client will send back through
#   the script, but still has all the needed info.  Returns a transformed
#   cookie, or undef if the cookie is invalid (e.g. comes from
#   the wrong host).
# A cookie is uniquely identified by the domain, path, and name, so this
#   transformation embeds the path and domain info into the "name".
# If $USE_DB_FOR_COOKIES is true, then store cookie in database instead,
#   and return undef to clear any Set-Cookie: header.
# This doesn't handle multiple comma-separated cookies-- possible, but
#   which seems a slight contradiction between the HTTP spec (section 4.2
#   of both HTTP 1.0 and 1.1 specs) and the cookie spec at
#   http://www.netscape.com/newsref/std/cookie_spec.html.
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_cookie_to_client() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of this routine.

sub cookie_to_client {
    my($cookie, $source_path, $source_server)= @_ ;
    my($name, $value, $expires_clause, $path, $domain, $secure_clause, $httponly_clause) ;
    my($new_name, $new_value, $new_cookie) ;

    # Start last four regexes with ";" to avoid extracting from name=value.
    # Cookie values aren't supposed to have commas, per the spec, but at least
    #   one site (go.com, using the Barista server) violates this.  So for now,
    #   allow commas in $value.
    # Cookie values aren't supposed to have spaces, either, but some sites
    #   have spaces in cookie values.  Thus, we allow spaces too.  :P
    #($name, $value)=   $cookie=~ /^\s*([^=;,\s]*)\s*=?\s*([^;,\s]*)/ ;
    ($name, $value)=   $cookie=~ /^\s*([^=;,\s]*)\s*=?\s*([^;]*)/ ;
    ($expires_clause)= $cookie=~ /;\s*(expires\s*=[^;]*)/i ;
    ($path)=     $cookie=~ /;\s*path\s*=\s*([^;,\s]*)/i ;  # clash w/ ;-params?
    ($domain)=         $cookie=~ /;\s*domain\s*=\s*([^;,\s]*)/i ;
    ($secure_clause)=  $cookie=~ /;\s*(secure\b)/i ;
    ($httponly_clause)=  $cookie=~ /;\s*(HttpOnly\b)/i ;

    # Path defaults to either the path of the URL that sent the cookie, or '/'.
    #   See comments above $COOKIE_PATH_FOLLOWS_SPEC for more details.
    $path=  $COOKIE_PATH_FOLLOWS_SPEC  ? $source_path  : '/'  if $path eq '' ;

    # Domain must be checked for validity: defaults to the server that sent
    #   the cookie; otherwise, must match end of that server name, and must
    #   contain at least two dots if in one of these seven top-level domains,
    #   three dots otherwise.
    # As it turns out, hostnames ending in extraneous dots, like
    #   "slashdot.org.." resolve to the hostname without the dots.  So we
    #   need to guard against malicious cookie servers getting around the
    #   two/three-dot requirement this way.
    # Unfortunately, the three-dot rule is not always followed; consider
    #   for example the domain "google.de".  Probably because of such domains,
    #   browsers seem to only require two dots.  Thus, do the same here,
    #   unless $RESPECT_THREE_DOT_RULE is set.
    # Browsers also allow domains such as "example.com", i.e. missing the
    #   leading dot.  :P  So, prepend a dot in such situations; only do this
    #   if the 3-dot rule is already relaxed.
    if ($domain eq '') {
	$domain= $source_server ;
    } else {
	$domain=~ s/\.*$//g ;  # removes trailing dots!
	$domain=~ tr/././s ;   # ... and double dots for good measure.
	# Allow $domain to match domain-minus-leading-dot (erroneously),
	#   because that's how browsers do it.
	return undef
	    if ($source_server!~ /\Q$domain\E$/) and ('.'.$source_server ne $domain) ;
	if ($RESPECT_THREE_DOT_RULE) {
	    return(undef) unless
		( ( ($domain=~ tr/././) >= 3 ) ||
		  ( ($domain=~ tr/././) >= 2 &&
		    $domain=~ /\.(com|edu|net|org|gov|mil|int)$/i )
		) ;
	} else {
	    if (($domain=~ tr/././) < 2) {
		return undef  if $domain=~ /^\./ ;
		$domain= '.' . $domain ;
		return undef  if ($domain=~ tr/././) < 2 ;
	    }
	}
    }


    # Change $expires_clause to make it a session cookie if so configured.
    # Don't do so if the cookie expires in the past, which means a deleted cookie.
    if ($SESSION_COOKIES_ONLY && $expires_clause ne '') {
	my($expires_date)= $expires_clause=~ /^expires\s*=\s*(.*)$/i ;
	$expires_clause= ''  if &date_is_after($expires_date, $now) ;
    }


    # If we're using a server-side database to store cookies, then store it and
    #   return undef to clear the existing Set-Cookie: header.
    return undef
	if $USE_DB_FOR_COOKIES and
	   store_cookie_in_db($name, $value, $expires_clause, $path, $domain, $secure_clause, $httponly_clause) ;


    # This is hereby the transformed format: name is COOKIE;$name;$path;$domain
    #   (the three values won't already have semicolons in them); value is
    #   $value;$secure_clause .  Both name and value are then cookie_encode()'d.
    #   The name contains everything that identifies the cookie, and the value
    #   contains all info we might care about later.
    $new_name= &cookie_encode("COOKIE;$name;$path;$domain") ;

    # New value is "$value;$secure_clause", then cookie_encode()'d.
    $new_value= &cookie_encode("$value;$secure_clause") ;


    # Create the new cookie from its components, removing the empty ones.
    # The new domain is this proxy server, which is the default if it is not
    #   specified.
    $new_cookie= join('; ', grep(length,
				 $new_name . '=' . $new_value,
				 $expires_clause,
				 'path=' . $ENV_SCRIPT_NAME . '/',
				 ($RUNNING_ON_SSL_SERVER ? ('secure') : () ),
				 $httponly_clause
		     )) ;
    return $new_cookie ;

}



# Returns a cookie that contains authentication information for a particular
#   realm and server.  The format of the cookie is:  The name is
#   AUTH;$URL_encoded_realm;$URL_encoded_server, and the value is the
#   base64-encoded "$username:$password" needed for the Authorization: header.
#   On top of that, both name and value are cookie_encode()'d.
# Leave the "expires" clause out, which means the cookie lasts as long as
#   the session, which is what we want.
# Note that auth cookies are NOT stored in a server-side database, for security
#   reasons.  Chances are there will never be enough auth cookies to overflow
#   the HTTP requests.
sub auth_cookie {
    my($username, $password, $realm, $server)= @_ ;

    $realm=~ s/(\W)/ '%' . sprintf('%02x',ord($1)) /ge ;
    $server=~ s/(\W)/ '%' . sprintf('%02x',ord($1)) /ge ;

    return join('', &cookie_encode("AUTH;$realm;$server"), '=',
		    &cookie_encode(&base64("$username:$password")),
		    '; path=' . $ENV_SCRIPT_NAME . '/' ) ;

}



# Generates a set of cookies that will delete the cookies contained in the
#   given cookie strings (e.g. from HTTP_COOKIE).  This is done by giving
#   each cookie an expiration time in the past, and setting their values
#   to "" for good measure.
# The input @cookies can each be a list of cookies separated by ";" .  The
#   cookies themselves can be either "name=value" or just "name".
# The return value is one long string of multiple "Set-Cookie:" headers.
# Slight quirk in Netscape and other browsers-- if cookie expiration is
#   set to the epoch time of "01-Jan-1970 00:00:00 GMT" (meaning second #0),
#   the cookie is treated as a session cookie instead of a deleted cookie.
#   Using second #1, i.e. "01-Jan-1970 00:00:01 GMT", causes the cookies to
#   be correctly deleted.

sub cookie_clearer {
    my(@cookies)= @_ ;   # may be one or more lists of cookies
    my($ret, $cname) ;

    foreach (@cookies) {
	foreach $cname ( split(/\s*;\s*/) ) {
	    $cname=~ s/=.*// ;      # change "name=value" to "name"
	    $ret.= "Set-Cookie: $cname=; expires=Thu, 01-Jan-1970 00:00:01 GMT; "
		 . "path=$ENV_SCRIPT_NAME/\015\012" ;
	}
    }
    return $ret ;
}


# Reads $session_id and $session_id_persistent from HTTP_COOKIE .
sub get_session_cookies {
    my($name, $value) ;

    foreach ( split(/\s*;\s*/, $ENV{HTTP_COOKIE}) ) {
	($name, $value)= split(/=/, $_) ;
	$session_id= $value, next  if $name eq 'S' ;
	$session_id_persistent= $value, next  if $name eq 'S2' ;
    }
}



#--------------------------------------------------------------------------
#    Utility routines
#--------------------------------------------------------------------------

# The following subroutine looks messy, but can be used to open any
#   TCP/IP socket in any Perl program.  Except for the &HTMLdie() part.
# Typeglobbing has trouble with mod_perl and tied filehandles, so pass socket
#   handle as a string instead (e.g. 'S'), or as a variable.
# Older versions created the packet structure with the old "pack('S n a4 x8')"
#   method.  However, some OS's (such as BSDI) vary from this, and it wouldn't
#   work with IPv6 either.  So now we use the more general functions, like
#   pack_sockaddr_in() from Socket.pm.  (IPv6 support may require other
#   changes too.)
sub newsocketto {
    my($S, $host, $port)= @_ ;
    my($hostaddr, $remotehost) ;

    # If $host is long integer like 3467251275, break it into a.b.c.d format.
    # This is for big-endian; reverse the list for little-endian.
    $host= join('.', $host>>24 & 255, $host>>16 & 255, $host>>8 & 255,
		     $host & 255)
	if $host=~ /^\d+$/ ;

    # Create the remote host data structure, from host name or IP address.
    # Note that inet_aton() handles both alpha names and IP addresses.
    $hostaddr= inet_aton($host)
	|| &HTMLdie("Couldn't find address for $host: $!") ;
#    $remotehost= pack('S n a4 x8', AF_INET, $port, $hostaddr) ;
    $remotehost= pack_sockaddr_in($port, $hostaddr) ;

    # If the target IP address is a banned host or network, die appropriately.
    # This assumes that IP address structs have the most significant byte first.
    # This is a quick addition that will be fleshed out in a later version.
    # This may not work with IPv6, depending on what inet_aton() returns then.
    for (@BANNED_NETWORK_ADDRS) {
	&banned_server_die() if $hostaddr=~ /^$_/ ;   # No URL forces a die
    }

    # Create the socket and connect to the remote host
    no strict 'refs' ;   # needed to use $S as filehandle
    socket($S, AF_INET, SOCK_STREAM, (getprotobyname('tcp'))[2])
	|| &HTMLdie("Couldn't create socket: $!") ;
    connect($S, $remotehost)
	|| &HTMLdie("Couldn't connect to $host:$port: $!") ;
    select((select($S), $|=1)[0]) ;      # unbuffer the socket
}


# Read a specific number of bytes from a socket, looping if necessary.
# Returns all bytes read (possibly less than $length), or undef on error.
# Typeglobbing *STDIN into *S doesn't seem to work with mod_perl 1.21, so
#   pass socket handle as a string instead (e.g. 'STDIN'), or as a variable.
# Using *S, the read() below immediately fails under mod_perl.
sub read_socket {
#    local(*S, $length)= @_ ;
    my($S, $length)= @_ ;
    my($ret, $numread, $thisread) ;

    #$numread= 0 ;
    no strict 'refs' ;   # needed to use $S as filehandle

    while (    ($numread<$length)
#	    && ($thisread= read(S, $ret, $length-$numread, $numread) ) )
	    && ($thisread= read($S, $ret, $length-$numread, $numread) ) )
    {
	$numread+= $thisread ;
    }
    return undef unless defined($thisread) ;

    return $ret ;
}


# Read a chunked body and footers from a socket; assumes that the
#   Transfer-Encoding: is indeed chunked.
# Returns the body and footers (which should then be appended to any
#   previous headers), or undef on error.
# For details of chunked encoding, see the HTTP 1.1 spec, e.g. RFC 2616
#   section 3.6.1 .
sub get_chunked_body {
    my($S)= @_ ;
    my($body, $footers, $chunk_size, $chunk) ;
    local($_) ;
    local($/)= "\012" ;

    # Read one chunk at a time and append to $body.
    # Note that hex() will automatically ignore a semicolon and beyond.
    no strict 'refs' ;     # needed to use $S as filehandle
    $body= '' ;            # to distinguish it from undef
    no warnings 'digit' ;  # to let hex() operate without warnings
    while ($chunk_size= hex(<$S>) ) {
	$body.= $chunk= &read_socket($S, $chunk_size) ;
	return undef unless length($chunk) == $chunk_size ;  # implies defined()
	$_= <$S> ;         # clear CRLF after chunk
    }

    # After all chunks, read any footers, NOT including the final blank line.
    while (<$S>) {
	last if /^(\015\012|\012)/  || $_ eq '' ;   # lines end w/ LF or CRLF
	$footers.= $_ ;
    }
    $footers=~ s/(\015\012|\012)[ \t]+/ /g ;       # unwrap long footer lines

    return wantarray  ? ($body, $footers)  : $body  ;
}



# This is a minimal routine that reads URL-encoded variables from a string,
#   presumably from something like QUERY_STRING.  If no string is passed,
#   it will read from either QUERY_STRING or STDIN, depending on
#   REQUEST_METHOD.  STDIN can't be read more than once for POST requests.
# It returns a hash.  In the event of multiple variables with the same name,
#   it concatenates the values into one hash element, delimiting with "\0".
# Returns undef on error.
sub getformvars {
    my($in)= @_ ;
    my(%in, $name, $value) ;

    # If no string is passed, read it from the usual channels.
    unless (defined($in)) {
	if ( ($ENV{'REQUEST_METHOD'} eq 'GET') ||
	     ($ENV{'REQUEST_METHOD'} eq 'HEAD') ) {
	    $in= $ENV{'QUERY_STRING'} ;
	} elsif ($ENV{'REQUEST_METHOD'} eq 'POST') {
	    return undef unless
		lc($ENV{'CONTENT_TYPE'}) eq 'application/x-www-form-urlencoded';
	    return undef unless defined($ENV{'CONTENT_LENGTH'}) ;
	    $in= &read_socket($STDIN, $ENV{'CONTENT_LENGTH'}) ;
	    # should we return undef if not all bytes were read?
	} else {
	    return undef ;   # unsupported REQUEST_METHOD
	}
    }

    foreach (split(/[&;]/, $in)) {
	s/\+/ /g ;
	($name, $value)= split('=', $_, 2) ;
	$name=~ s/%([\da-fA-F]{2})/ pack('C', hex($1)) /ge ;
	$value=~ s/%([\da-fA-F]{2})/ pack('C', hex($1)) /ge ;
	$in{$name}.= "\0" if defined($in{$name}) ;  # concatenate multiple vars
	$in{$name}.= $value ;
    }
    return %in ;
}



# For a given timestamp, returns a date in one of the following two forms,
#   depending on the setting of $use_dash:
#     "Wdy, DD Mon YYYY HH:MM:SS GMT"
#     "Wdy, DD-Mon-YYYY HH:MM:SS GMT"
# The first form is used in HTTP dates, and the second in Netscape's cookie
#   spec (although cookies sometimes use the first form, which seems to be
#   handled OK by most recipients).
# The first form is basically the date format in RFC 822 as updated in RFC
#   1123, except GMT is always used here.
sub rfc1123_date {
    my($time, $use_dash)= @_ ;
    my($s) =  $use_dash  ? '-'  : ' ' ;
    my(@t)= gmtime($time) ;

    return sprintf("%s, %02d$s%s$s%04d %02d:%02d:%02d GMT",
		   $WEEKDAY[$t[6]], $t[3], $MONTH[$t[4]], $t[5]+1900, $t[2], $t[1], $t[0] ) ;
}


# Returns true if $date1 is later than $date2.  Both parameters can be in
#   either rfc1123_date() format or the total-seconds format from time().
#   rfc1123_date() format is "Wdy, DD-Mon-YYYY HH:MM:SS GMT", possibly using
#   spaces instead of dashes.
# Returns undef if either date is invalid.
# A more general function would be un_rfc1123_date(), to take an RFC 1123 date
#   and return total seconds.
sub date_is_after {
    my($date1, $date2)= @_ ;
    my(@d1, @d2) ;

    # Trivial case when both are numeric.
    return ($date1>$date2)  if $date1=~ /^\d+$/ && $date2=~ /^\d+$/ ;

    # Get date components, depending on formats
    if ($date1=~ /^\d+$/) {
	@d1= (gmtime($date1))[3,4,5,2,1,0] ;
    } else {
	@d1= $date1=~ /^\w+,\s*(\d+)[ -](\w+)[ -](\d+)\s+(\d+):(\d+):(\d+)/ ;
	return undef unless @d1 ;
	$d1[1]= $UN_MONTH{lc($d1[1])} ;
	$d1[2]-= 1900 ;
    }
    if ($date2=~ /^\d+$/) {
	@d2= (gmtime($date2))[3,4,5,2,1,0] ;
    } else {
	@d2= $date2=~ /^\w+,\s*(\d+)[ -](\w+)[ -](\d+)\s+(\d+):(\d+):(\d+)/ ;
	return undef unless @d2 ;
	$d2[1]= $UN_MONTH{lc($d2[1])} ;
	$d2[2]-= 1900 ;
    }

    # Compare year, month, day, hour, minute, second in order.
    return ( ( $d1[2]<=>$d2[2] or $d1[1]<=>$d2[1] or $d1[0]<=>$d2[0] or
	       $d1[3]<=>$d2[3] or $d1[4]<=>$d2[4] or $d1[5]<=>$d2[5] )
	     > 0 ) ;
}



# Escape any &"<> chars to &xxx; and return resulting string.
# Also converts chars>127 to "&#nnn;" entities.
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_html_escape() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of this routine.
sub HTMLescape {
    my($s)= @_ ;
    $s=~ s/&/&amp;/g ;      # must be before all others
    $s=~ s/([^\x00-\x7f])/'&#' . ord($1) . ';'/ge ;
    $s=~ s/"/&quot;/g ;
    $s=~ s/</&lt;/g ;
    $s=~ s/>/&gt;/g ;
    return $s ;
}


# Unescape any &xxx; codes back to &"<> and return resulting string.
# Simplified version here; only includes &"<> and "&#nnn"-type entities.
# Some people accidentally leave off final ";", and some browsers support that
#   if the word ends there, so make the final ";" optional.
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_html_unescape() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of this routine.
sub HTMLunescape {
    my($s)= @_ ;
    $s=~ s/&quot\b;?/"/g ;
    $s=~ s/&lt\b;?/</g ;
    $s=~ s/&gt\b;?/>/g ;
    $s=~ s/&#(x)?(\w+);?/ $1 ? chr(hex($2)) : chr($2) /ge ;
    $s=~ s/&amp\b;?/&/g ;      # must be after all others
    return $s ;
}



# Base64-encode a string, except not inserting line breaks.
sub base64 {
    my($s)= @_ ;
    my($ret, $p, @c, $t) ;

    # Base64 padding is done with "=", but that's in the first 64 characters.
    #   So, use "@" as a placeholder for it until the tr/// statement.

    # For each 3 bytes, build a 24-bit integer and split it into 6-bit chunks.
    # Insert one or two padding chars if final substring is less than 3 bytes.
    while ($p<length($s)) {
	@c= unpack('C3', substr($s,$p,3)) ;
	$p+= 3 ;
	$t= ($c[0]<<16) + ($c[1]<<8) + $c[2] ;     # total 24-bit integer
	$ret.= pack('C4',     $t>>18,
			     ($t>>12)%64,
		    (@c>1) ? ($t>>6) %64 : 64,
		    (@c>2) ?  $t     %64 : 64 ) ;  # "@" is chr(64)
    }

    # Translate from bottom 64 chars into base64 chars, plus @ to = conversion.
    $ret=~ tr#\x00-\x3f@#A-Za-z0-9+/=# ;

    return $ret ;
}


# Opposite of base64() .
sub unbase64 {
    my($s)= @_ ;
    my($ret, $p, @c, $t, $pad) ;

    $pad++ if $s=~ /=$/ ;
    $pad++ if $s=~ /==$/ ;

    $s=~ tr#A-Za-z0-9+/##cd ;          # remove non-allowed characters
    $s=~ tr#A-Za-z0-9+/#\x00-\x3f# ;   # for speed, translate to \x00-\x3f

    # For each 4 chars, build a 24-bit integer and split it into 8-bit bytes.
    # Remove one or two chars from result if input had padding chars.
    while ($p<length($s)) {
	@c= unpack('C4', substr($s,$p,4)) ;
	$p+= 4 ;
	$t= ($c[0]<<18) + ($c[1]<<12) + ($c[2]<<6) + $c[3] ;
	$ret.= pack('C3', $t>>16, ($t>>8) % 256, $t % 256 ) ;
    }
    chop($ret) if $pad>=1 ;
    chop($ret) if $pad>=2 ;

    return $ret ;
}



# Convert a string from UTF-16 encoding to UTF-8.
sub un_utf16 {
    my($s)= @_ ;

    Encode::from_to($$s, "utf-16", "utf-8") ;  # converts in-place
}



# Read an entire file into a string and return it; return undef on error.
# Does NOT check for any security holes in $fname!
sub readfile {
    my($fname)= @_ ;
    my($ret) ;
    local(*F, $/) ;

    open(F, "<$fname") || return undef ;
    undef $/ ;
    $ret= <F> ;
    close(F) ;

    return $ret ;
}



sub random_string {
    my($len)= @_ ;
    my @chars= (0..9, 'a'..'z', 'A'..'Z') ;
    return join('', map { $chars[rand(scalar @chars)] } 1..$len) ;
}



# Simple, general-purpose HTTP client.  The HTTP client in http_get() is too
#   specialized and non-modular to use for anything but the primary resource.
# This leaves the connection open, i.e. a persistent connection, because that's
#   needed for the purpose this routine was written for (the external tests).
# This routine expects a pointer to a hash containing "host", "port", "socket",
#   and "open" elements, plus a $request_uri string.  In the hash, iff "open"
#   is false, then a new socket is opened, in the interest of persistent
#   connections.  "host", "port", and "socket" (a string name of a filehandle)
#   are assumed to be unchanging.
# Note that this HTTP client is missing many features, such as proxy support,
#   SSL support, and authentication.  Eventually, http_get() may be restructured
#   to be more modular and support what we need here.
# This is partially copied from http_get().  For more commenting, see that
#   routine, in the similar sections as below.
sub http_get2 {
    my($c, $request_uri)= @_ ;
    my($s, $status, $status_code, $headers, $body, $footers, $rin, $win, $num_tries) ;
    local($/)= "\012" ;

    no strict 'refs' ;    # needed for symbolic references

    # Using "$c->{socket}" causes syntax errors in some places, so alias it to $s.
    $s= $c->{socket} ;

    # For some reason, under mod_perl, occasionally the socket response is
    #   empty.  It may have something to do with the scope of the filehandles.
    #   Work around it with this hack-- if such occurs, retry the routine up
    #   to three times.
    RESTART: {
	# Create a new socket if a persistent one isn't lingering from last time.
	# Ideally we'd test eof() on the socket at the end of this routine, but
	#   that may only fail after many seconds.  So, here we assume the socket
	#   is still usable if it's not '' and if we can write to it.
	vec($win= '', fileno($s), 1)= 1 if defined(fileno($s)) ;
	if (!$c->{open} || !select(undef, $win, undef, 0)) {
	    &newsocketto($c->{socket}, $c->{host}, $c->{port}) ;
	    $c->{open}= 1 ;
	}

	# Print the simple request.
	print $s 'GET ', $request_uri, " HTTP/1.1\015\012",
		 'Host: ', $c->{host}, (($c->{port}==80)  ? ''  : ":$c->{port}"), "\015\012",
		 "\015\012" ;


	vec($rin= '', fileno($s), 1)= 1 ;
	select($rin, undef, undef, 60)
	    || &HTMLdie("No response from $c->{host}:$c->{port}") ;

	$status= <$s> ;

	# hack hack....
	unless ($status=~ m#^HTTP/#) {
	    $c->{open}= 0 ;
	    redo RESTART if ++$num_tries<3 ;
	    &HTMLdie("Invalid response from $c->{host}: [$status]") ;
	}
    }


    # Loop to get $status and $headers until we get a non-100 response.
    # See comments in http_get(), above the similar block.
    do {
	($status_code)= $status=~ m#^HTTP/\d+\.\d+\s+(\d+)# ;

	$headers= '' ;
	do {
	    $headers.= $_= <$s> ;    # $headers includes last blank line
	} until (/^(\015\012|\012)$/) || $_ eq '' ; #lines end w/ LF or CRLF

	$status= <$s> if $status_code == 100 ;  # re-read for next iteration
    } until $status_code != 100 ;

    # Unfold long header lines, a la RFC 822 section 3.1.1
    $headers=~ s/(\015\012|\012)[ \t]+/ /g ;

    # Read socket body depending on how length is determined; see RFC 2616 (the
    #   HTTP 1.1 spec), section 4.4.
    if ($headers=~ /^Transfer-Encoding:[ \t]*chunked\b/mi) {
	($body, $footers)= &get_chunked_body($s) ;
	&HTMLdie(&HTMLescape("Error reading chunked response from $c->{host} ."))
	    unless defined($body) ;
	$headers=~ s/^Transfer-Encoding:[^\012]*\012?//mig ;
	$headers=~ s/^(\015\012|\012)/$footers$1/m ;

    } elsif ($headers=~ /^Content-Length:[ \t]*(\d+)/mi) {
	$body= &read_socket($s, $1) ;

    } else {
	undef $/ ;
	$body= <$s> ;  # ergo won't be persistent connection
	close($s) ;
	$c->{open}= 0 ;
    }

    # If server doesn't support persistent connections, then close the socket.
    # We would test eof($s) here, but that causes a long wait.
    if ($headers=~ /^Connection:.*\bclose\b/mi || $status=~ m#^HTTP/1\.0#) {
	close($s) ;
	$c->{open}= 0 ;
    }

    return $body ;
}



#--------------------------------------------------------------------------
#    Output routines
#--------------------------------------------------------------------------


# Returns the complete HTML to be inserted at the top of a page, which may
#   consist of the URL entry form and/or a custom insertion in $INSERT_HTML
#   or $INSERT_FILE.
# [Actually, this is only the insertion in the <body>-- the URL form and
#   possibly the user's insertion-- not the JS insertion in the <head>.]
# As an important side effect, both %IN_CUSTOM_INSERTION and %in_mini_start_form
#   are set in set_custom_insertion() and mini_start_form(), respectively.
#   These are used later to handle certain JavaScript.
# Note that any insertion should not have any relative URLs in it, because
#   there's no good base URL to resolve them with.  See the comments where
#   $INSERT_HTML and $INSERT_FILE are set.
# Use the global, persistent variable $CUSTOM_INSERTION to hold the custom
#   insertion from $INSERT_HTML or $INSERT_FILE.  Set it the first time it's
#   needed (every time for a CGI script, once for a mod_perl script).  This
#   minimizes how often an inserted file is opened and read.
# $INSERT_HTML takes precedence over $INSERT_FILE.
# The inserted entry form is never anonymized.
sub full_insertion {
    my($URL, $in_top_frame)= @_ ;
    my($ret, $form, $insertion) ;
    $form= &mini_start_form($URL, $in_top_frame) if $e_insert_entry_form ;

    if (($INSERT_HTML ne '') || ($INSERT_FILE ne '')) {
	&set_custom_insertion if $CUSTOM_INSERTION eq '' ;

	# The insertion should not have relative URLs, but in case it does
	#   provide a base URL of this script for lack of anything better.
	#   It's erroneous, but it avoids unpredictable behavior.  $url_start
	#   is also required for proxify_html(), but it has already been set.
	# We can't do this only once to initialize, we must do this for each
	#   run, because user config flags might change from run to run.
	# NOTE!  If we don't use 0 in &proxify_html() here we'll recurse!
	if ($ANONYMIZE_INSERTION) {
	    local($base_url)= $script_url ;
	    &fix_base_vars ;
	    $insertion= &proxify_html(\$CUSTOM_INSERTION,0) ;
	} else {
	    $insertion= $CUSTOM_INSERTION ;
	}
    }

    $ret= $FORM_AFTER_INSERTION  ? $insertion . $form  : $form . $insertion ;

    my(%inc_by)= %in_mini_start_form ;
    foreach (keys %IN_CUSTOM_INSERTION) {
	$inc_by{$_}+= $IN_CUSTOM_INSERTION{$_} ;
    }
    $ret.= "<script type=\"text/javascript\">\n"
	 . "if (typeof(_proxy_jslib_increments)=='object') {\n"
	 . join('', map { "    _proxy_jslib_increments['$_']= $inc_by{$_} ;\n" }
			keys %inc_by)
	 . "}\n</script>\n"
	if %inc_by ;

    $ret= "\n<div>\n$ret</div>\n\n<div id=\"_proxy_css_main_div\" style=\"position:relative\">\n" ;

    return $ret ;
}


# Returns the HTML needed for JavaScript support, the insertion into the <head>
#   of the document.
sub js_insertion {
    my($base_url_jsq, $default_script_type_jsq, $default_style_type_jsq,
       $p_cookies_are_banned_here, $p_doing_insert_here, $p_session_cookies_only,
       $p_cookie_path_follows_spec, $p_respect_three_dot_rule,
       $p_allow_unproxified_scripts, $p_use_db_for_cookies, $cookies_from_db_jsq) ;
    # Create JS double-quoted string of base URL and other vars.
    ($base_url_jsq=            $base_url           )=~ s/(["\\])/\\$1/g ;
    ($default_script_type_jsq= $default_script_type)=~ s/(["\\])/\\$1/g ;
    ($default_style_type_jsq=  $default_style_type )=~ s/(["\\])/\\$1/g ;
    ($cookies_from_db_jsq= $USE_DB_FOR_COOKIES
	?  get_cookies_from_db($path, $host, $port, $scheme, 1)  : '')=~ s/(["\\])/\\$1/g ;
    $p_cookies_are_banned_here=   $cookies_are_banned_here   ? 'true'  : 'false' ;
    $p_doing_insert_here=         $doing_insert_here         ? 'true'  : 'false' ;
    $p_session_cookies_only=      $SESSION_COOKIES_ONLY      ? 'true'  : 'false' ;
    $p_cookie_path_follows_spec=  $COOKIE_PATH_FOLLOWS_SPEC  ? 'true'  : 'false' ;
    $p_respect_three_dot_rule=    $RESPECT_THREE_DOT_RULE    ? 'true'  : 'false' ;
    $p_allow_unproxified_scripts= $ALLOW_UNPROXIFIED_SCRIPTS ? 'true'  : 'false' ;
    $p_use_db_for_cookies=        $USE_DB_FOR_COOKIES        ? 'true'  : 'false' ;

    return '<script type="text/javascript" src="'
	 . &HTMLescape($url_start . &wrap_proxy_encode('x-proxy://scripts/jslib'))
	 . "\"></script>\n"
	 . qq(<script type="text/javascript">_proxy_jslib_pass_vars("$base_url_jsq",$p_cookies_are_banned_here,$p_doing_insert_here,$p_session_cookies_only,$p_cookie_path_follows_spec,$p_respect_three_dot_rule,$p_allow_unproxified_scripts,"$RTMP_SERVER_PORT","$default_script_type_jsq","$default_style_type_jsq",$p_use_db_for_cookies,"$cookies_from_db_jsq");</script>\n) ;
}


# Set $CUSTOM_INSERTION from the correct source.  Also set %IN_CUSTOM_INSERTION
#   according to its contents.  This is needed for JavaScript handling, to
#   handle arrays like document.forms[] etc. that reference page elements in
#   order.  Insertions at the top of the page throw these arrays off, so we
#   must compensate by incrementing those subscripts by the number of forms,
#   links, etc. in the top insertion.  The counts in %IN_CUSTOM_INSERTION are
#   used for the custom insertion; elements in the inserted entry form are
#   handled elsewhere.
# The relevant arrays in the document object are applets[], embeds[], forms[],
#   ids[], layers[], anchors[], images[], and links[].  The first five
#   correspond directly to HTML tag names; the last three must be handled
#   individually.  The patterns below to detect <a href> and <a name> aren't
#   exact, but should work in almost all cases.  The pattern to detect tags
#   isn't even perfect-- it fails on script blocks, etc.  However, errors would
#   be rare and fairly harmless, and this whole situation is pretty rare anyway.
sub set_custom_insertion {
    return if $CUSTOM_INSERTION ne '' ;
    return unless ($INSERT_HTML ne '') || ($INSERT_FILE ne '') ;

    # Read $CUSTOM_INSERTION from the appropriate source.
    $CUSTOM_INSERTION= ($INSERT_HTML ne '')   ? $INSERT_HTML  : &readfile($INSERT_FILE) ;

    # Now, set counts in %IN_CUSTOM_INSERTION.
    %IN_CUSTOM_INSERTION= () ;
    foreach (qw(applet embed form id layer)) {
	$IN_CUSTOM_INSERTION{$_.'s'}++ while $CUSTOM_INSERTION=~ /<\s*$_\b/gi ;
    }
    $IN_CUSTOM_INSERTION{anchors}++ while $CUSTOM_INSERTION=~ /<\s*a\b[^>]*\bname\s*=/gi ;
    $IN_CUSTOM_INSERTION{links}++   while $CUSTOM_INSERTION=~ /<\s*a\b[^>]*\bhref\s*=/gi ;
    $IN_CUSTOM_INSERTION{images}++  while $CUSTOM_INSERTION=~ /<\s*img\b/gi ;
}



# Print the footer common to most error responses
sub footer {
    my($rightlink)= $NO_LINK_TO_START
	? ''
	: qq(<a href="$script_url"><i>Restart</i></a>) ;

    my $proxified_homepage= &HTMLescape(full_url('http://www.jmarshall.com/tools/cgiproxy/')) ;
    my $download_link= &HTMLescape(full_url("http://www.jmarshall.com/tools/cgiproxy/releases/cgiproxy.latest.tar.gz")) ;

    return <<EOF ;
<p>
<hr>
<table width="100%"><tr>
<td align=left>
<i><a href="$proxified_homepage">CGIProxy $PROXY_VERSION</a>
   (<a href="$download_link">download</a>)</i>
</td>
<td align=right>
$rightlink
</td>
</tr></table>
<p>
</body>
</html>
EOF
}



# Return the contents of the top frame, i.e. the one with whatever insertion
#   we have-- the entry form and/or the inserted HTML or file.
sub return_top_frame {
    my($enc_URL)= @_ ;
    my($body, $insertion) ;
    my($date_header)= &rfc1123_date($now, 0) ;

    # Redirect any links to the top frame.  Make sure any called routines know
    #   this by setting $base_unframes.  Also use $url_start_noframe to make
    #   sure any links with a "target" attribute that are followed from an
    #   anonymized insertion have the frame flag unset, and therefore have
    #   their own correct insertion.
    local($base_unframes)= 1 ;
    local($url_start)= $url_start_noframe ;

    $body= &full_insertion(&wrap_proxy_decode($enc_URL), 1) ;

    my $response= <<EOR . footer() ;
<html>
<head><base target="_top"></head>
<body>
$body
</body>
</html>
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}


# Return a frame document that puts the insertion in the top frame and the
#   actual page in the lower frame.  Both of these will have the is_in_frame
#   flag set.
# MUST be careful to set $is_in_frame flag!  Else will recurse!
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_return_frame_doc() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   mostly a Perl-to-JavaScript translation of this routine.
sub return_frame_doc {
    my($enc_URL, $title)= @_ ;
    my($qs_URL, $top_URL, $page_URL) ;
    my($date_header)= &rfc1123_date($now, 0) ;

    ($qs_URL= $enc_URL) =~ s/([^\w.-])/ '%' . sprintf('%02x',ord($1)) /ge ;
    $top_URL= &HTMLescape($url_start_inframe
			. &wrap_proxy_encode('x-proxy://frames/topframe?URL=' . $qs_URL) ) ;
    $page_URL= &HTMLescape($url_start_inframe . $enc_URL) ;


    my $response= <<EOR . footer() ;
<html>
<head>
<title>$title</title>
</head>
<frameset rows="$INSERTION_FRAME_HEIGHT,*">
    <frame src="$top_URL"  name="_proxy_jslib_insertion_frame">
    <frame src="$page_URL" name="_proxy_jslib_main_frame">
</frameset>
</html>
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# When an image should be blanked, returns either a transparent 1x1 GIF or
#   a 406 result ("Not Acceptable").
sub skip_image {
    &return_empty_gif if $RETURN_EMPTY_GIF ;

    my($date_header)= &rfc1123_date($now, 0) ;
    print $STDOUT "$HTTP_1_X 406 Not Acceptable\015\012$session_cookies${NO_CACHE_HEADERS}Date: $date_header\015\012\015\012" ;
    die "exiting" ;
}


# Return a 1x1 transparent GIF.  Yes, that's an inlined 43-byte GIF.
sub return_empty_gif {
    my($date_header)= &rfc1123_date($now, 0) ;

    print $STDOUT <<EOF ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: image/gif
Content-Length: 43

GIF89a\x01\0\x01\0\x80\0\0\0\0\0\xff\xff\xff\x21\xf9\x04\x01\0\0\0\0\x2c\0\0\0\0\x01\0\x01\0\x40\x02\x02\x44\x01\0\x3b
EOF

    die "exiting" ;
}



# Returns a 302 redirection response to $location, with optional extra headers.
# $other_headers must be complete with final "\015\12", etc.
sub redirect_to {
    my($location, $other_headers)= @_ ;
    print $STDOUT "$HTTP_1_X 302 Moved\015\012", $session_cookies, $NO_CACHE_HEADERS,
		  "Date: ", &rfc1123_date($now,0), "\015\012",
		  $other_headers,
		  "Location: $location\015\012\015\012" ;

    die "exiting" ;
}



# Present the initial entry form
sub show_start_form {
    my($msg, $URL)= @_ ;
    my($method, $action, $flags, $cookies_url, $safe_URL, $jslib_block,
       $onsubmit, $onload) ;
    my($date_header)= &rfc1123_date($now, 0) ;

    $msg= "\n<h1><font color=green>$msg</font></h1>"  if $msg ne '' ;

    $method= $USE_POST_ON_START   ? 'post'   : 'get' ;

    $action=      &HTMLescape( $url_start . &wrap_proxy_encode('x-proxy://start') ) ;
    $cookies_url= &HTMLescape( $url_start . &wrap_proxy_encode('x-proxy://cookies/manage') ) ;
    $safe_URL= &HTMLescape($URL) ;

    # Encode the URL before submitting, if so configured.  Start it with "\x01" or
    #   "\x7f" (depending on the browser) to indicate that it's encoded.
    if ($ENCODE_URL_INPUT) {
	$jslib_block= '<script src="'
		    . &HTMLescape($url_start . &wrap_proxy_encode('x-proxy://scripts/jslib'))
		    . "\"></script>\n" ;
	my $encode_prefix= $ENV{HTTP_USER_AGENT}=~ /Chrome|Safari/  ? "\\x7f"  : "\\x01" ;
	$onsubmit= qq( onsubmit="if (!this.URL.value.match(/^$encode_prefix/)) this.URL.value= '$encode_prefix'+_proxy_jslib_wrap_proxy_encode(this.URL.value) ; return true") ;
	$onload= qq( onload="document.URLform.URL.focus() ; if (document.URLform.URL.value.match(/^$encode_prefix/)) document.URLform.URL.value= _proxy_jslib_wrap_proxy_decode(document.URLform.URL.value.replace(/$encode_prefix/, ''))") ;
    } else {
	$jslib_block= $onsubmit= '' ;
	$onload= ' onload="document.URLform.URL.focus()"' ;
    }

    # Include checkboxes if user config is allowed.
    if ($ALLOW_USER_CONFIG) {
	my($rc_on)= $e_remove_cookies     ? ' checked'  : '' ;
	my($rs_on)= $e_remove_scripts     ? ' checked'  : '' ;
	my($fa_on)= $e_filter_ads         ? ' checked'  : '' ;
	my($br_on)= $e_hide_referer       ? ' checked'  : '' ;
	my($if_on)= $e_insert_entry_form  ? ' checked'  : '' ;
	$flags= <<EOF ;
<br><input type=checkbox id="rc" name="rc"$rc_on><label for="rc"> Remove all cookies (except certain proxy cookies)</label>
<br><input type=checkbox id="rs" name="rs"$rs_on><label for="rs"> Remove all scripts (recommended for anonymity)</label>
<br><input type=checkbox id="fa" name="fa"$fa_on><label for="fa"> Remove ads</label>
<br><input type=checkbox id="br" name="br"$br_on><label for="br"> Hide referrer information</label>
<br><input type=checkbox id="if" name="if"$if_on><label for="if"> Show URL entry form</label>
EOF
    }

    my $response= <<EOR . footer() ;
<html>
<head>
$jslib_block
<title>Start Using CGIProxy</title>
</head>
<body$onload>
$msg
<h1>CGIProxy</h1>
<p>Start browsing through this CGI-based proxy by entering a URL below.
Only HTTP and FTP URLs are supported.  Not all functions will work
(e.g. some Java applets), but most pages will be fine.

<form name="URLform" action="$action" method="$method"$onsubmit>
<input name="URL" size=66 value="$safe_URL">
$flags
<p><input type=submit value="   Begin browsing   ">
</form>

<h3><a href="$cookies_url">Manage cookies</a></h3>
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOR . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOR

    die "exiting" ;
}



# Returns a mini version of the start form, as a string.  It requires
#   $url_start and $URL to be already set.
# To support this correctly in a frame, point it to target="_top" and use
#   $url_start_noframe in the action.
# Put the cookie management in the full window, and when the user "returns to
#   browsing" the frame flag will cause the frames to reload correctly.
# Since this may be in a page with strict e.g. XHTML checking, the HTML here
#   must be strictly valid.
sub mini_start_form {
    my($URL, $in_top_frame)= @_ ;
    my($method, $action, $flags, $table_open, $table_close,
       $cookies_url, $from_param, $safe_URL, $onsubmit, $onfocus) ;

    $method= $USE_POST_ON_START   ? 'post'   : 'get' ;
    $action= &HTMLescape( $url_start_noframe . &wrap_proxy_encode('x-proxy://start') ) ;
    $safe_URL= &HTMLescape($URL) ;

    # In "manage cookies" link, provide a way to return to page user came from.
    # Exclude certain characters from URL-encoding, to make URL more readable
    #   in the event it's not obscured.  Unfortunately, ":" and "/" are
    #   reserved in query component (RFC 2396), so we can't exclude them.
    # Don't confusing "URL-encoding" with the "encoding of the URL"!  The
    #   latter uses proxy_encode().  Unfortunate language.
    $from_param= &wrap_proxy_encode($URL) ;   # don't send unencoded URL
    $from_param=~ s/([^\w.-])/ '%' . sprintf('%02x',ord($1)) /ge ;
    $cookies_url= $url_start_noframe . &wrap_proxy_encode('x-proxy://cookies/manage')
		. '?from=' . $from_param ;
    $cookies_url= &HTMLescape($cookies_url) ;

    # Create "UP" link.
    my($scheme_authority, $up_path)= $URL=~ m{^([^:/?#]+://[^/?#]*)([^?#]*)} ;
    $up_path=~ s#[^/]*.$##s ;
    my($safe_up_URL)= &HTMLescape( $url_start_noframe . &wrap_proxy_encode("$scheme_authority$up_path") ) ;
    my($up_link)= $up_path ne ''
	? qq(&nbsp;&nbsp;<a href="$safe_up_URL" target="_top" style="color:#0000FF;">[&nbsp;UP&nbsp;]</a>)
	: '' ;

    # Alter various HTML depending on whether we're in the top frame or not.
    ($table_open, $table_close)= $in_top_frame
	? ('', '')
	: ('<table border="1" cellpadding="5"><tr><td align="center" bgcolor="white"><font color="black">',
	   '</font></td></tr></table>') ;

    # Set global hash %in_mini_start_form according to how many each of applets,
    #   embeds, form, ids, layers, anchors, images, and links there are in this
    #   form.  It's used for handling certain JavaScript, later.
    # This isn't a persistent variable because it could vary from run to run.
    %in_mini_start_form= ('forms', 1, 'links', (($up_path ne '')  ? 2  : 1)) ;

    # Encode the URL before submitting, if so configured.  Start it with "\x01"
    #   or "\x7f" (depending on the browser) to indicate that it's encoded.
    # Possible clash when a page has another element named "URL"; revisit if needed.
    if ($ENCODE_URL_INPUT) {
	$needs_jslib= 1 ;
	my $encode_prefix= $ENV{HTTP_USER_AGENT}=~ /Chrome|Safari/  ? "\\x7f"  : "\\x01" ;
	$onsubmit= qq( onsubmit="if (!this.URL.value.match(/^$encode_prefix/)) this.URL.value= '$encode_prefix'+_proxy_jslib_wrap_proxy_encode(this.URL.value) ; return true") ;
	$onfocus= qq( onfocus="if (this.value.match(/^$encode_prefix/)) this.value= _proxy_jslib_wrap_proxy_decode(this.value.replace(/\\$encode_prefix/, ''))") ;
    } else {
	$onsubmit= '' ;
    }


    # Display one of two forms, depending on whether user config is allowed.
    if ($ALLOW_USER_CONFIG) {
	my($rc_on)= $e_remove_cookies     ? ' checked=""'  : '' ;
	my($rs_on)= $e_remove_scripts     ? ' checked=""'  : '' ;
	my($fa_on)= $e_filter_ads         ? ' checked=""'  : '' ;
	my($br_on)= $e_hide_referer       ? ' checked=""'  : '' ;
	my($if_on)= $e_insert_entry_form  ? ' checked=""'  : '' ;

# jsm-- remove for production release, plus in form below.
my($safe_URL2) ;
($safe_URL2= $URL)=~ s/([^\w.-])/ '%' . sprintf('%02x',ord($1)) /ge ;
$safe_URL2= "http://jmarshall.com/bugs/report.cgi?URL=$safe_URL2&version=$PROXY_VERSION&rm=$RUN_METHOD" ;
$safe_URL2= &HTMLescape(&full_url($safe_URL2)) ;

	return <<EOF ;
<form name="URLform" action="$action" method="$method" target="_top"$onsubmit>
<center>
$table_open
&nbsp;&nbsp;Location&nbsp;via&nbsp;proxy:<input name="URL" size="66" value="$safe_URL"$onfocus /><input type="submit" value="Go" />
$up_link&nbsp;&nbsp;
<br /><a href="$safe_URL2"><font color="red">[Report a bug]</font></a>
&nbsp;&nbsp;<a href="$cookies_url" target="_top" style="color:#0000FF;">[Manage&nbsp;cookies]</a>&nbsp;&nbsp;
<font size="-1"><input type="checkbox" id="rc" name="rc"$rc_on /><label for="rc" style="display: inline">&nbsp;No&nbsp;cookies</label>
&nbsp;&nbsp;<input type="checkbox" id="rs" name="rs"$rs_on /><label for="rs" style="display: inline">&nbsp;No&nbsp;scripts</label>
&nbsp;&nbsp;<input type="checkbox" id="fa" name="fa"$fa_on /><label for="fa" style="display: inline">&nbsp;No&nbsp;ads</label>
&nbsp;&nbsp;<input type="checkbox" id="br" name="br"$br_on /><label for="br" style="display: inline">&nbsp;No&nbsp;referrer</label>
&nbsp;&nbsp;<input type="checkbox" id="if" name="if"$if_on /><label for="if" style="display: inline">&nbsp;Show&nbsp;this&nbsp;form</label>&nbsp;&nbsp;
</font>
$table_close
</center>
</form>
EOF

    # If user config isn't allowed, then show a different form.
    } else {
	return <<EOF ;
<form name="URLform" action="$action" method="$method" target="_top"$onsubmit>
<center>
$table_open
Location&nbsp;via&nbsp;proxy:<input name="URL" size=66 value="$safe_URL"$onfocus><input type=submit value="Go">
$up_link
&nbsp;&nbsp;<a href="$cookies_url" target="_top">[Manage&nbsp;cookies]</a>
$table_close
</center>
</form>
EOF
    }

}



# Display cookies to the user and let user selectively delete them.
# No expiration date is displayed because to make that available would
#   require embedding it in every cookie.
sub manage_cookies {
    my($qs)= @_ ;
    my($return_url, $action, $clear_cookies_url, $cookie_rows, $auth_rows,
       $cookie_header_row, $from_tag) ;
    my(@cookies, @auths, $name, $value, $type, @n, $delete_cb,
       $cname, $path, $domain, $cvalue, $secure,
       $realm, $server, $username) ;

    my($date_header)= &rfc1123_date($now, 0) ;

    my(%in)= &getformvars($qs) ;

    # $in{'from'} is already proxy_encoded
    $return_url= &HTMLescape( $url_start . $in{'from'} ) ;
    $action=     &HTMLescape( $url_start . &wrap_proxy_encode('x-proxy://cookies/update') ) ;

    # Create "clear cookies" link, preserving any query string.
    $clear_cookies_url= $url_start . &wrap_proxy_encode('x-proxy://cookies/clear') ;
    $clear_cookies_url.= '?' . $qs    if $qs ne '' ;
    $clear_cookies_url= &HTMLescape($clear_cookies_url) ;   # probably never necessary

    # Include from-URL in form if it's available.
    $from_tag= '<input type=hidden name="from" value="' . &HTMLescape($in{'from'}) . '">'
	if $in{'from'} ne '';

    # First, create $cookie_rows and $auth_rows from $ENV{'HTTP_COOKIE'}.
    # Note that the "delete" checkboxes use the encoded name as their identifier.
    # With minor rewriting, this could sort cookies e.g. by server.  Is that
    #   preferred?  Note that the order of cookies in $ENV{'HTTP_COOKIE'} has
    #   meaning.
    foreach ( split(/\s*;\s*/, $ENV{'HTTP_COOKIE'}) ) {
	($name, $value)= split(/=/, $_, 2) ;  # $value may contain "="
	$delete_cb= '<input type=checkbox name="delete" value="'
		  . &base64($name) . '">' ;
	$name= &cookie_decode($name) ;
	$value= &cookie_decode($value) ;
	($type, @n)= split(/;/, $name) ;
	if ($type eq 'COOKIE') {
	    next if $USE_DB_FOR_COOKIES ;
	    ($cname, $path, $domain)= @n ;
	    ($cvalue, $secure)= split(/;/, $value) ;

	    push(@cookies, {delete_cb => $delete_cb,
			    domain => $domain,
			    path => $path,
			    name => $cname,
			    value => $cvalue,
			    secure => $secure}) ;

	} elsif ($type eq 'AUTH') {
	    # format of auth cookie's name is AUTH;$enc_realm;$enc_server
	    ($realm, $server)= @n ;
	    $realm=~  s/%([\da-fA-F]{2})/ pack('C', hex($1)) /ge ;
	    $server=~ s/%([\da-fA-F]{2})/ pack('C', hex($1)) /ge ;
	    ($username)= split(/:/, &unbase64($value)) ;

	    push(@auths, {delete_cb => $delete_cb,
			  server => $server,
			  username => $username,
			  realm => $realm}) ;

	}
    }

    # Grab cookies from the database if using it for cookies.
    if ($USE_DB_FOR_COOKIES) {
	@cookies= get_all_cookies_from_db() ;
	$_->{delete_cb}= '<input type=checkbox name="delete" value="'
		       . &base64("$_->{domain};$_->{path};$_->{name}") . '">'
	    foreach @cookies ;
    }

    @cookies= sort {$a->{domain} cmp $b->{domain} or
		    $a->{path}   cmp $b->{path}   or
		    $a->{name}   cmp $b->{name}} @cookies ;
    @auths= sort {$a->{server}   cmp $b->{server} or 
		  $a->{realm}    cmp $b->{realm}  or
		  $a->{username} cmp $b->{username}} @auths ;


    # Set $cookie_rows and $auth_rows, with defaults as needed.
    if ($USE_DB_FOR_COOKIES) {
	$cookie_header_row= <<EOH ;
<tr><th>Delete this cookie?</th>
    <th>For server names ending in:</th>
    <th>... and a path starting with:</th>
    <th>Expires</th>
    <th>Secure?</th>
    <th>HTTP only?</th>
    <th>Cookie name</th>
    <th align=left>Value</th>
</tr>
EOH

	$cookie_rows= join('', map {sprintf("<tr align=center><td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td align=left>%s</td></tr>\n",
					    $_->{delete_cb},
					    &HTMLescape($_->{domain}),
					    &HTMLescape($_->{path}),
					    &HTMLescape($_->{expires}) || '(session)',
					    $_->{secure}  ? 'Yes'  : 'No',
					    $_->{httponly}  ? 'Yes'  : 'No',
					    &HTMLescape($_->{name}),
					    &HTMLescape($_->{value}) )}
				   @cookies) ;

	# If $cookie_rows is empty, set appropriate message.
	$cookie_rows= "<tr><td colspan=8 align=center>&nbsp;<br><b><font face=Verdana size=2>You are not currently sending any cookies through this proxy.</font></b><br>&nbsp;</td></tr>\n"
	    if $cookie_rows eq '' ;


    } else {
	$cookie_header_row= <<EOH ;
<tr><th>Delete this cookie?</th>
    <th>For server names ending in:</th>
    <th>... and a path starting with:</th>
    <th>Secure?</th>
    <th>Cookie name</th>
    <th align=left>Value</th>
</tr>
EOH

	$cookie_rows= join('', map {sprintf("<tr align=center><td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td align=left>%s</td></tr>\n",
					    $_->{delete_cb},
					    &HTMLescape($_->{domain}),
					    &HTMLescape($_->{path}),
					    $_->{secure}  ? 'Yes'  : 'No',
					    &HTMLescape($_->{name}),
					    &HTMLescape($_->{value}) )}
				   @cookies) ;

	# If $cookie_rows is empty, set appropriate message.
	$cookie_rows= "<tr><td colspan=6 align=center>&nbsp;<br><b><font face=Verdana size=2>You are not currently sending any cookies through this proxy.</font></b><br>&nbsp;</td></tr>\n"
	    if $cookie_rows eq '' ;
    }


    $auth_rows= join('', map {sprintf("<tr align=center><td>%s</td>\n<td>%s</td>\n<td>%s</td>\n<td>%s</td></tr>\n",
					    $_->{delete_cb},
					    &HTMLescape($_->{server}),
					    &HTMLescape($_->{realm}),
					    &HTMLescape($_->{username}) )}
			      @auths) ;

    $auth_rows= "<tr><td colspan=4 align=center>&nbsp;<br><b><font face=Verdana size=2>You are not currently authenticated to any sites through this proxy.</font></b><br>&nbsp;</td></tr>\n"
	if $auth_rows eq '' ;


    my $response= <<EOR . footer() ;
<html>
<head>
<title>CGIProxy Cookie Management</title>
</head>
<body>
<h3><a href="$return_url">Return to browsing</a></h3>
<h3><a href="$clear_cookies_url">Delete all cookies</a></h3>
<h1>Here are the cookies you're using through CGIProxy:</h1>

<form action="$action" method=post>
$from_tag

<p><font color=red>
<input type=submit value="Delete selected cookies">
</font>

<p>
<table bgcolor="#ccffff" border=1>
$cookie_header_row
$cookie_rows
</table>

<h3>Authentication cookies:</h3>
<table bgcolor="#ccffcc" border=1>
<tr><th>Delete this cookie?</th>
    <th>Server</th>
    <th>User</th>
    <th>Realm</th>
</tr>
$auth_rows
</table>

<p><font color=red>
<input type=submit value="Delete selected cookies">
</font>
</form>

EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
Cache-Control: no-cache
Pragma: no-cache
Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# Present the user with a special form that lets them enter authentication.
# The target URL is proxy_encoded in the form, for obscurity.
# Uses POST, because a GET request would show auth info in a logged URL.
sub get_auth_from_user {
    my($server, $realm, $URL, $tried)= @_ ;
    my($action, $msg) ;
    my($date_header)= &rfc1123_date($now, 0) ;

    $server= &HTMLescape($server) ;
    $realm=  &HTMLescape($realm) ;
    $URL=    &HTMLescape(&wrap_proxy_encode($URL)) ;

    $action= &HTMLescape( $url_start . &wrap_proxy_encode('x-proxy://auth/make_auth_cookie') ) ;

    $msg= "<h3><font color=red>Authorization failed.  Try again.</font></h3>"
	if $tried ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Enter username and password for $realm at $server</title></head>
<body>
<h1>Authorization Required</h1>
$msg

<form action="$action" method=post>
<input type=hidden name="s" value="$server">
<input type=hidden name="r" value="$realm">
<input type=hidden name="l" value="$URL">

<table border=1 cellpadding=5>
<tr><th bgcolor="#ff6666">
    Enter username and password for <nobr>$realm</nobr> at $server:</th></tr>
<tr><td bgcolor="#b0b0b0">
    <table cellpadding=0 cellspacing=0>
    <tr><td>Username:</td><td><input name="u" size=20></td></tr>
    <tr><td>Password:</td><td><input type=password name="p" size=20></td>
	<td>&nbsp;&nbsp;&nbsp;<input type=submit value="OK"></tr>
    </table>
</table>
</form>
<p>This requires cookie support turned on in your browser.
<p><i><b>Note:</b> Anytime you use a proxy, you're trusting the owner of that
proxy with all information you enter, including your name and password here.
This is true for <b>any</b> proxy, not just this one.
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
Cache-Control: no-cache
Pragma: no-cache
Date: $date_header
Content-type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# Alert the user to an unsupported URL, with this intermediate page.
sub unsupported_warning {
    my($URL)= @_ ;
    my($date_header)= &rfc1123_date($now, 0) ;

    &redirect_to($URL) if $URL eq 'about:blank' ;
    &redirect_to($URL) if $QUIETLY_EXIT_PROXY_SESSION ;

    # Prevent a XSS attack.
    $URL= &HTMLescape($URL) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>WARNING: Entering non-anonymous area!</title></head>
<body>
<h1>WARNING: Entering non-anonymous area!</h1>
<h3>This proxy only supports HTTP and FTP.  Any browsing to another URL will
be directly from your browser, and no longer anonymous.</h3>
<h3>Follow the link below to exit your anonymous browsing session, and
continue to the URL non-anonymously.</h3>
<blockquote><tt><a href="$URL">$URL</a></tt></blockquote>
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}


# Alert the user that SSL is not supported, with this intermediate page.
sub no_SSL_warning {
    my($URL)= @_ ;
    my($date_header)= &rfc1123_date($now, 0) ;

    &redirect_to($URL) if $QUIETLY_EXIT_PROXY_SESSION ;

    # Prevent a XSS attack.
    $URL= &HTMLescape($URL) ;
    my $homepage= &HTMLescape(full_url('http://www.jmarshall.com/tools/cgiproxy/')) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>WARNING: SSL not supported, entering non-anonymous area!</title></head>
<body>
<h1>WARNING: SSL not supported, entering non-anonymous area!</h1>
<h3>This proxy as installed does not support SSL, i.e. URLs that start
with "https://".  To support SSL, the proxy administrator needs to install
the Net::SSLeay Perl module (perhaps by running "<code>nph-proxy.cgi install-modules</code>"),
and then this proxy will automatically support SSL (the
<a href="$homepage">CGIProxy site</a>
has more info).  In the meantime, any browsing to an "https://" URL will
be directly from your browser, and no longer anonymous.</h3>
<h3>Follow the link below to exit your anonymous browsing session, and
continue to the URL non-anonymously.</h3>
<blockquote><tt><a href="$URL">$URL</a></tt></blockquote>
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}


# Alert the user that gzip is not supported.
sub no_gzip_die {
    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Compressed content not supported, but was sent by server.</title></head>

<body>
<h1>Compressed content not supported, but was sent by server.</h1>
<p>The server at $host:$port replied with compressed content, even though it
was told not to.  That server is either misconfigured, or has a bug.
<p>To support compressed content, the proxy administrator needs to install
the IO::Compress::Gzip Perl package-- perhaps by running
"<code>nph-proxy.cgi install-modules</code>"-- and then this proxy will
automatically support it.  (Note that the IO::Compress::Gzip package is already
included in Perl 5.9.4 or later.)
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# Return "403 Forbidden" message if the target server is forbidden.
sub banned_server_die {
    my($URL)= @_ ;
    my($date_header)= &rfc1123_date($now, 0) ;

    # Here, only quietly redirect out if we get a URL.  This allows calling
    #   routines to force an error, such as when using @BANNED_NETWORKS, or
    #   when a URL is not available.
    &redirect_to($URL) if $QUIETLY_EXIT_PROXY_SESSION && ($URL ne '') ;

    my $response= <<EOR . footer() ;
<html>
<head><title>The proxy can't access that server, sorry.</title></head>
<body>
<h1>The proxy can't access that server, sorry.</h1>
<p>The owner of this proxy has restricted which servers it can access,
presumably for security or bandwidth reasons.  The server you just tried
to access is not on the list of allowed servers.
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 403 Forbidden
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# Return "403 Forbidden" message if the user's IP address is disallowed.
sub banned_user_die {
    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>You are not allowed to use this proxy, sorry.</title></head>
<body>
<h1>You are not allowed to use this proxy, sorry.</h1>
<p>The owner of this proxy has restricted which users are allowed to use it.
Based on your IP address, you are not an authorized user.
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 403 Forbidden
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# If so configured, disallow browsing back through this same script.
sub loop_disallowed_die {
    my($URL)= @_ ;
    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Proxy cannot loop back through itself</title></head>
<body>
<h1>Proxy cannot loop back through itself</h1>
<p>The URL you tried to access would cause this proxy to access itself,
which is redundant and probably a waste of resources.  The owner of this
proxy has configured it to disallow such looping.
<p>Rather than telling the proxy to access the proxy to access the desired
resource, try telling the proxy to access the resource directly.  The link
below <i>may</i> do this.
<blockquote><tt><a href="$URL">$URL</a></tt></blockquote>
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 403 Forbidden
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# Die if we try to retrieve a secure page while not running on a secure server,
#   because it's a security hole.
sub insecure_die {
    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Retrieval of secure URLs through a non-secure proxy is forbidden.</title>
<body>
<h1>Retrieval of secure URLs through a non-secure proxy is forbidden.</h1>
<p>This proxy is running on a non-secure server, which means that retrieval
of pages from secure servers is not permitted.  The danger is that the user
and the end server may believe they have a secure connection between them,
while in fact the link between the user and this proxy is insecure and
eavesdropping may occur.  That's why we have secure servers, after all.
<p>This proxy must run on a secure server before being allowed to retrieve
pages from other secure servers.
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# Return "403 Forbidden" response for script content-type.
sub script_content_die {
    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Script content blocked</title></head>
<body>
<h1>Script content blocked</h1>
<p>The resource you requested (or were redirected to without your knowledge)
is apparently an executable script.  Such resources have been blocked by this
proxy, presumably for your own protection.
<p>Even if you're sure you want the script, you can't get it through this
proxy the way it's configured.  If permitted, try browsing through this proxy
without removing scripts.  Otherwise, you'll need to reconfigure the proxy or
find another way to get the resource.
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 403 Forbidden
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# If images are forbidden, return either a "403 Forbidden" message or a
#   1x1 transparent GIF.
sub non_text_die {
    &return_empty_gif if $RETURN_EMPTY_GIF ;

    my($date_header)= &rfc1123_date($now, 0) ;

    my $homepage= &HTMLescape(full_url('http://www.jmarshall.com/tools/cgiproxy/')) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Proxy cannot forward non-text files</title></head>
<body>
<h1>Proxy cannot forward non-text files</h1>
<p>Due to bandwidth limitations, the owner of this particular proxy is
forwarding only text files.  For best results, turn off automatic image
loading if your browser lets you.
<p>If you need access to images or other binary data, route your browser
through another proxy (or install one yourself--
<a href="$homepage">it's easy</a>).
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 403 Forbidden
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}



# Die if the Encode module is needed but not found.
sub no_Encode_die {
    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Page uses UTF-16 encoding, which is unsupported by this version
      of Perl</title></head>
<body>
<h1>Page uses UTF-16 encoding, which is unsupported by this version of Perl</h1>
<p>The page you requested appears to be in Unicode's UTF-16 format.  This is
not supported by the version of Perl running on this server (more exactly, the
"Encode" Perl module could not be found).
<p>To support UTF-16, please upgrade to Perl version 5.8.0 or later.
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}


sub malformed_unicode_die {
    my($charset)= @_ ;
    my($date_header)= &rfc1123_date($now, 0) ;

    my $response= <<EOR . footer() ;
<html>
<head><title>Page has malformed Unicode</title></head>
<body>
<h1>Page has malformed Unicode</h1>
<p>This page says it's using the charset "$charset", but the content could not
be correctly decoded as that charset.  Please notify the owner of the page
in question.
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X 200 OK
$session_cookies${NO_CACHE_HEADERS}Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}


sub return_401_response {
    my($client_http_version)= @_ ;
    my($date_header)= &rfc1123_date($now, 0) ;
    $HTTP_1_X=  $NOT_RUNNING_AS_NPH   ? 'Status:'   : $client_http_version ;

    print $STDOUT <<EOR ;
$HTTP_1_X 401 Unauthorized
Date: $date_header
WWW-Authenticate: Basic realm="proxy"

EOR
    # Do not exit-- this is called in a while() loop from handle_http_request() .
}


# Die, outputting HTML error page, with optional response code and title.
sub HTMLdie {
    my($msg, $title, $status)= @_ ;

    # Don't use HTML if run from the command line.
    die "$msg\n" if $RUN_METHOD eq 'fastcgi' or $RUN_METHOD eq 'embedded' ;

    $title= 'CGIProxy Error' if $title eq '' ;
    $status= '200 OK' if $status eq '' ;
    my($date_header)= &rfc1123_date($now, 0) ;

    # In case this is called early, set $HTTP_1_X to something that works.
    $HTTP_1_X=  $NOT_RUNNING_AS_NPH   ? 'Status:'   : "HTTP/1.0"
	if $HTTP_1_X eq '' ;

    my $response= <<EOR . footer() ;
<html>
<head><title>$title</title></head>
<body>
<h1>$title</h1>
<h3>$msg</h3>
EOR

    my $cl= length($response) ;
    print $STDOUT <<EOH . $response ;
$HTTP_1_X $status
Cache-Control: no-cache
Pragma: no-cache
Date: $date_header
Content-Type: text/html
Content-Length: $cl

EOH
    die "exiting" ;
}




#-----------------------------------------------------------------------
#  support for proxifying JavaScript
#-----------------------------------------------------------------------

# This routine modifies JavaScript code so that it works correctly through this
#   script.  This includes altering URL accesses to go through this script,
#   altering the reading and writing of cookies, and anthing else that's needed
#   to make script operation privacy-safe and transparent to the user.  The
#   $top_level parameter indicates whether this call is nested or not; it's
#   useful for only inserting a call to _proxy_jslib_flush_write_buffers() when
#   needed (slightly hacky).
# The return value is a two-item array consisting of the proxified JS string,
#   and that end part of $in that could not be proxified (which is usually
#   discarded by the caller).
# Elsewhere in this script, there is a library of JavaScript functions that are
#   called by code this routine produces.  If this routine generates any code
#   that uses that library, then it sets the global variable $needs_jslib=1 .
#   (It's not reset to false when the output code doesn't use the library,
#   since this routine may be called many times for one page.)
# THIS ROUTINE MAY NOT BE FOOLPROOF!!!  I can say that this script proxifies
#   JavaScript better than any similar software I've seen, and I know of no
#   privacy holes, but I can't guarantee there are none at this time.  If you
#   find a way to construct JavaScript that will not be correctly proxified
#   here, then please let me know.  If extreme privacy is critical to you,
#   then I recommend you turn off scripts in your browser.
# The current approach is to replace certain constructs with calls to
#   _proxy_jslib_handle(), _proxy_jslib_assign(), or _proxy_jslib_assign_rval()
#   in the JS library.  To do this: The input is read one token at a time (see
#   the routine set_RE_JS() below for details about tokenization), and when a
#   token is found that may need proxifying, it is replaced by a call to one of
#   those three functions, depending on whether it is being read/called or
#   assigned.  This requires, during tokenization, keeping track of the current
#   "term", by which I mean what the JS spec calls LeftHandSideExpression, one
#   value or variable, like one term if you consider an expression to be like a
#   polynomial, that one term which may have several object references or
#   method calls in it.  (Harder to explain than to understand.)  The term
#   (object) leading up to the token is passed to _proxy_jslib_handle() and
#   _proxy_jslib_assign() so they can test its type and access the property
#   through it.  Also passed to _proxy_jslib_handle() are the property name
#   (either a token or read from between "[]"), and the current value of the
#   property/variable (only needed when the object is null).  Passed to
#   _proxy_jslib_assign() are the "prefix" (i.e. "++", "--", or "delete"), the
#   leading term/object, the property name, the operator that causes the
#   assignment, and the right-hand expression it's being assigned to.  If there
#   is no leading term/object, then _proxy_jslib_assign_rval() is called
#   instead, with the prefix, the property name, the operator, the expression
#   it's being assigned to, and the property's current value.
# Also done in this routine are things like incrementing subscripts of e.g.
#   document.forms[] and other arrays, and changing references from
#   "_proxy_jslib_..." to "_proxy1_jslib_..." etc. to keep the libraries
#   separate when chaining proxies.  A lot of code just deals with keeping
#   $term_so_far accurate in different situations.
# _proxy_jslib_handle() returns the same function for e.g. "a" in
#   "d.e= a" as for "a(c)", even though their "this"'s should be
#   different-- former "this" is "d", and latter "this" is "window".  This
#   is handled by testing "this===window", which should be true whenever
#   the returned function is not called as a method, including when it is
#   called immediately as in "a(c)".
#
# [Note: the next section needs to be updated, as more things need to be
#   handled than those listed below.]
#
# Below are everything in core and client-side JavaScript that need to be
#   handled, according to a read of the reference sections of "JavaScript: The
#   Definitive Guide", 4th Edition, by David Flanagan, published by O'Reilly.
#   The only exceptions are minor and would not open privacy holes, such as
#   exact screen coordinates being off because of our insertions, or certain
#   DOM arrays being shifted because of our insertions (similar to the forms[]
#   etc. arrays we try to handle, as listed below).
#
# Here are the network-related things in JS that are handled by this script:
#   Window.open(), Document.write(), Document.writeln(), Document.close(),
#     Location.replace(), Layer.load(), Window.setInterval(),
#     Window.setTimeout(), HTMLElement.setAttribute(),
#     HTMLElement.setAttributeNode(), Node.appendChild(), Node.insertBefore(),
#     Node.replaceChild, CSS*.insertRule(), HTMLElement.insertAdjacentHTML()
#     (MSIE only), Window.navigate() (MSIE only), eval(), and many others are
#     handled in _proxy_jslib_handle().
#   All setting of src, href, background, lowsrc, action, useMap, longDesc,
#     cite, codeBase, profile, cssText, nodeValue, and location properties are
#     handled in _proxy_jslib_assign().  Also handled there are any setting of
#     innerHTML, outerHTML, or outerText properties, since they are defined by
#     HTMLElement and may be inherited by many different objects.  Also handled
#     in _proxy_jslib_assign() are any setting of the various read/write
#     properties of Link and Location objects that would cause a page to load.
#     There are several other things that _proxy_jslib_assign() handles.
#   If "location" is assigned without a leading object, then it is handled by
#     _proxy_jslib_assign_rval().
#   Cookies are handled-- reading of them in _proxy_jslib_handle(), and setting
#     of them in _proxy_jslib_assign().
#   "new Function(...)" is handled with _proxy_jslib_new_function(), since it
#     contains JS code that may need to be proxified.
#   These eight array properties of the document object are incremented as
#     needed, according to what's in the insertions:  applets[], embeds[],
#     forms[], ids[], layers[], anchors[], images[], and links[].
#   (.on* events don't need changing, since they're set to a function object,
#       unlike HTML event attributes, which are set to a string containing
#       JavaScript code.)
#
# NOTE: IF YOU MODIFY THIS ROUTINE, then be sure to review and possibly
#   modify the corresponding routine _proxy_jslib_proxify_js() in the
#   JavaScript library, far below in the routine return_jslib().  It is
#   a Perl-to-JavaScript translation of this routine.

sub proxify_js {
    my($in, $top_level, $with_level, $in_new_statement)= @_ ;
    $with_level||= 0 ;
    $in_new_statement||= 0 ;

    # Declaring variables here rather than in blocks below is a little faster.
    my(@out, $element, $token, $last_token, $new_last_token, $newline_since_last_token, $div_ok,
       $term_so_far, $prefix, $sub_expr, $op, $new_val, $cur_val_str,
       $in_braces, $in_func, $expr, $next_expr,
       $var_decl, $var, $eq, $value, $skip1, $skip2, $funcname, $with_obj, $code, $paren,
       $closequote1, $closequote2) ;

    # $does_write has to be communicated out of nested calls, so it's a global.
    #   Kind of hacky.
    $does_write= 0  if $top_level ;

    # Some sites erroneously have HTML comments in <script> blocks, which
    #   browsers try to work around.  :P  For now, remove one-line HTML
    #   comments and declarations from the start of a script block.
    1 while ($in=~ s/^\s*(?:<!--.*?-->\s*)+//
	  or $in=~ s/^\s*(?:<!.*?>\s*)+//    ) ;

    # MSIE fails when uncommented "-->" is encountered in the middle of a
    #   script, like when we insert "_proxy_jslib_flush_write_buffers()" at
    #   the end.  Thus, remove leading "<!--" and trailing "-->".
    # Also remove the remainder of the first line after the "<!--".
    $in=~ s/^\s*<!--[^\n]*(.*)-->\s*$/$1/s ;


    # Note that these patterns contain an embedded set of parentheses that
    #   only match if the input element is a token.
    # Correction:  Because of Perl's long-string-literal bug, there are two
    #   additional sets of embedded parentheses, which may match /'/ or /"/ .
  OUTER:
    while ($div_ok  ? $in=~ /\G($RE_JS_INPUT_ELEMENT_DIV)/gco
		    : $in=~ /\G($RE_JS_INPUT_ELEMENT_REG_EXP)/gco) {

	($element, $token, $closequote1, $closequote2)= ($1, $2, $3, $4) ;

	# To work around Perl's long-string-literal bug, read in rest of
	#   string literal if needed.
	if ($token=~ /^['"]/ && !$closequote1 && !$closequote2) {
	    last unless &get_string_literal_remainder(\$in, \$token) ;
	    $element= $token ;
	}

	# If a token was gotten, then set $div_ok according to the token.
	#   Until we get a more complete parser, this is a pretty good guess.
	#   Note that here, "token" also includes DivPunctuator and
	#   RegularExpressionLiteral.
	# DivPunctuator may come after: certain reserved words, identifiers,
	#   the four punctuators ") ] ++ --", numeric and string literals,
	#   and regular expression literals.  To match identifiers but not
	#   the wrong reserved words, it's probably easier to include all
	#   identifiers, then just exclude those reserved words which may
	#   precede RegularExpressionLiteral.  The last line of the pattern
	#   below tests the start of the token for several possible token
	#   types, combined into one pattern.
	# Reserved words that may precede DivPunctuator are qw(this null true false);
	#   reserved words that may precede RegularExpressionLiteral are
	#   qw(case delete do else in instanceof new return throw typeof void).
	# NOTE: We no longer use this regex here, but instead set $div_ok
	#   in each appropriate block of code below.  This saves about 5%
	#   of the entire call to proxify_js().  (We still use the regex in
	#   get_next_js_expr(), however.)

	#if (defined($token)) {
	#    $div_ok= $token=~ m#^(?:\)|\]|\+\+|--)$|
	#			^(?!(?:case|delete|do|else|in|instanceof|new|return|throw|typeof|void)$)
	#			 (?:\pL|[\$_\\0-9'"]|\.\d|/..)#x ;
	#}


	$newline_since_last_token= 1 if $element=~ /^$RE_JS_LINE_TERMINATOR$/o ;
	$new_last_token= '' ;

	# Keep track of whether we're in a function, to correctly handle returns.
	$in_braces++ if $token eq '{' ;
	$in_braces-- if $token eq '}' ;
	$in_func= 0 if $in_braces==0 ;


	# Now, handle cases depending on value of $token.


	# Only allow whitespace within a term, not comments, or else removing
	#   the final "." gets messy later.  Don't remove white space
	#   altogether, since it's needed to separate tokens correctly.  Line
	#   terminators also have to be preserved, for the sake of automatic
	#   semicolon insertion and other syntactic constructs.
	if ($token eq '') {
	    if ($term_so_far ne '') {
		if ($element=~ /$RE_JS_LINE_TERMINATOR/o) {
		    $term_so_far.= "\n" ;
		} else {
		    $term_so_far.= ' ' ;
		}
	    } else {
		push(@out, $element) ;
	    }


	# Increment identifiers from other libraries, to allow chaining of
	#   multiple proxies and to close a privacy hole.
	} elsif ($token=~ s/^_proxy(\d*)_/'_proxy'.($1+1).'_'/e) {
	    $term_so_far.= $token ;
	    $div_ok= 1 ;


	# Treat these as beginning a term.
	# Due to Perl's long-string-literal bug, string literals are matched
	#   by /^['"]/ rather than by $RE_JS_STRING_LITERAL.
	#} elsif ($token=~ /^(?:$RE_JS_NUMERIC_LITERAL|$RE_JS_STRING_LITERAL|$RE_JS_REGULAR_EXPRESSION_LITERAL)$/o) {
	} elsif ($token=~ /^(?:$RE_JS_NUMERIC_LITERAL|$RE_JS_REGULAR_EXPRESSION_LITERAL)$/o
		 or $token=~ /^['"]/) {
	    push(@out, $prefix, $term_so_far) ;
	    $prefix= '' ;
	    $term_so_far= $token ;
	    $div_ok= 1 ;


	# Now all input elements are handled except identifiers (including
	#   reserved words) and all punctuators (including DivPunctuator).
	# All punctuators end a term except for .[(, which each need a special
	#   block here to handle them; all punctuators that are
	#   AssignmentOperator or ++/-- must also be handled specially.


	# Handle increment and decrement operators, and "delete", using this
	#   simplification:  ++/-- is post- if there's a term so far and
	#   not a newline since the last token, and pre- otherwise.
	#   Pre- operators become the "prefix" parameter in the call to
	#   _proxy_jslib_assign(); with post- operators, $prefix and
	#   $term_so_far are pushed onto @out, then the operator itself.
	#   Note that $term_so_far may have already been transformed during
	#   the processing of a previous token.
	# Handle case when parentheses surround the term, e.g. "delete(a.b)" .
	} elsif ($token eq '++' or $token eq '--' or $token eq 'delete') {
	    # Handle "-->" instead of "--" if needed.
	    if ($token eq '--' and $in=~ /\G\s*>/gco) {
		push(@out, $prefix, $term_so_far, '-->') ;
		$prefix= $term_so_far= '' ;
	    } elsif (($term_so_far ne '') and !$newline_since_last_token) {
		push(@out, $prefix, $term_so_far, $token) ;
		$prefix= $term_so_far= '' ;
		$div_ok= 1 ;
	    } else {
		push(@out, $prefix, $term_so_far) ;
		$prefix= $term_so_far= '' ;
		my $start_paren= $in=~ /\G$RE_JS_SKIP*\(/gco ;
		my($o, $p)= &get_next_js_term(\$in) ;
		last unless defined($p) ;
		last if $start_paren and !($in=~ /\G$RE_JS_SKIP*\)/gco) ; 
		if ($o ne '') {
		    push(@out, " _proxy_jslib_assign('$token', (" . (&proxify_js($o, 0, $with_level))[0] . "), (" . (&proxify_js($p, 0, $with_level))[0] . "), '')" ) ;
		} else {
		    # Note that $p is guaranteed to be a quoted identifier here.
		    $p=~ s/^'|'$//g ;
		    if ($token eq 'delete') {
			push(@out, "delete $p");
		    } else {
			push(@out, "($p= _proxy_jslib_assign_rval('$token', '$p', '', '', (typeof $p=='undefined' ? void 0 : $p)))") ;
		    }
		}
		$div_ok= 1 ;

#		$prefix= $token ;
	    }


	# eval() is a special case.  It should normally be followed by a
	#   parenthesis, in which case we transform "eval(expr)" into
	#   "eval(_proxy_jslib_proxify_js(expr))".
	# If it's not followed by a parenthesis, then that means the code
	#   is probably trying to assign something to the eval function itself.
	#   By spec, this may be treated as an error.  We handle it in the
	#   next block using _proxy_jslib_handle(), though imperfectly (e.g.
	#   when eval is replaced by a function, local variables are no longer
	#   in scope).
	# When its argument is not a primitive string, eval() returns its
	#   argument unchanged, which mucks this code up a bit.  As an imperfect
	#   solution, this is handled in _proxy_jslib_proxify_js(), by having it
	#   return its argument unchanged if it's not a string.
	} elsif (($token eq 'eval') && $in=~ /\G($RE_JS_SKIP*\()/gco) {
	    $needs_jslib= 1 ;
	    $term_so_far.= $token . $1 . '_proxy_jslib_proxify_js(('
			 . (&proxify_js(&get_next_js_expr(\$in,1), 0, $with_level))[0]
			 . "), 0, $with_level) )" ;
	    last unless $in=~ /\G\)/gc ;
	    $div_ok= 1 ;


	# Here, explicitly handle all properties and methods that need special
	#   treatment.  Property names only are listed, and sorted out in the
	#   all-purpose routines _proxy_jslib_handle(), _proxy_jslib_assign(),
	#   and _proxy_jslib_assign_rval().
	# For document.write() and document.writeln(), note that the writing of
	#   one e.g. tag can be split among several write() statements.  So for
	#   the parsing of its output to happen correctly, for each JS block we
	#   accumulate a buffer of all write() output and then proxify and flush
	#   it as much as possible, leaving the remainder (e.g. a partial tag or
	#   an incomplete <script> or <style> block) in the buffer.
	# Element and Node have many properties which are inherited by many
	#   other objects.  Thus, their properties "innerHTML" through
	#   "nodeValue" below will be handled regardless of object type.
	#} elsif ($RE_JS_SET_TRAPPED_PROPERTIES{$token}) {
	} elsif ($token=~ /^(?:open|assign|write|writeln|close|replace|load|eval
			       |setInterval|setTimeout|toString|String
			       |src|currentSrc|href|background|lowsrc|action|formAction|location|poster
			       |URL|url|newURL|oldURL|referrer|baseURI
			       |useMap|longDesc|cite|codeBase|profile
			       |cssText|insertRule|setStringValue|setProperty
			       |backgroundImage|content|cursor|listStyleImage
			       |host|hostname|pathname|port|protocol|search
			       |setNamedItem
			       |innerHTML|outerHTML|outerText|body
			       |getElementById|getElementsByTagName
			       |appendChild|replaceChild|insertBefore|text|textContent
			       |insertAdjacentHTML
			       |setAttribute|setAttributeNode|getAttribute
			       |nodeValue
			       |value|cookie|domain|frames|parent|top|opener
			       |execScript|execCommand|navigate
			       |showModalDialog|showModelessDialog
			       |LoadMovie
			       |origin|postMessage|pushState|replaceState
			    )$/x) {
	    $needs_jslib= 1 ;
	    $does_write||= ($token eq 'write') || ($token eq 'writeln') || ($token eq 'eval') ;

	    # Handle automatic semicolon insertion.  For more notes about
	    #   automatic semicolon insertion, see comments in
	    #   get_next_js_expr() below.
	    if ($newline_since_last_token
		and $last_token=~ m#^(?:\)|\]|\+\+|--)$|
				    ^(?!(?:case|delete|do|else|in|instanceof|new|typeof|void|function|var)$)
				     (?:\pL|[\$_\\0-9'"]|\.\d|/..)#x )
	    {
		push(@out, $prefix, $term_so_far) ;
		$prefix= $term_so_far= '' ;
	    }

	    # Remove "." and possible trailing white space from $term_so_far.
	    #   (Comments are no longer included within $term_so_far.)
	    my $had_dot= $term_so_far=~ s/\.((?>$RE_JS_WHITE_SPACE+)|$RE_JS_LINE_TERMINATOR)*\z// ;

	    # Transform to either _proxy_jslib_handle() or _proxy_jslib_assign() call.

	    # Peek ahead to see if the next token is an open parenthesis
	    my $old_pos= pos($in) ;
	    my $next_is_paren= $in=~ /\G$RE_JS_SKIP*\(/gco  ? 1  : 0 ;
	    pos($in)= $old_pos ;

	    # First, avoid modifying property names in object literals, which
	    #   are preceded by "{" or "," and followed by ":" .
	    # Not the cleanest here. but should work.
	    if ($last_token=~ /^[{,]$/ and $in=~ /\G($RE_JS_SKIP*:)/gco) {
		push(@out, $prefix, $term_so_far, $token, $1) ;
		$prefix= $term_so_far= '' ;
		$new_last_token= ':' ;
		$div_ok= 0 ;

	    # Avoid proxifying "String" if it's not followed by "(", to allow
	    #   static method calls to pass unchanged.
	    } elsif ($token eq 'String' and !$next_is_paren) {
		$term_so_far.= '.' if $had_dot ;
		$term_so_far.= $token;
		$div_ok= 1;

	    } elsif ($prefix ne '') {
		if ($term_so_far eq '') {
		    push(@out, ($with_level
				? " $token= _proxy_jslib_with_assign_rval(_proxy_jslib_with_objs, '$prefix', '$token', '', '', $token)"
				: " $token= _proxy_jslib_assign_rval('$prefix', '$token', '', '', (typeof $token=='undefined' ? void 0 : $token))") ) ;
		} else {
		    $term_so_far= " _proxy_jslib_assign('$prefix', $term_so_far, '$token', '', '')" ;
		}
		$prefix= '' ;
		$new_last_token= ')' ;
		$div_ok= 1 ;
	    } elsif ($in=~ /\G$RE_JS_SKIP_NO_LT*(\+\+|--)/gco) {
		$op= $1 ;
		if ($term_so_far eq '') {
		    push(@out, ($with_level
				? " $token= _proxy_jslib_with_assign_rval(_proxy_jslib_with_objs, '', '$token', '$op', '', $token)"
				: " $token= _proxy_jslib_assign_rval('', '$token', '$op', '', (typeof $token=='undefined' ? void 0 : $token))") ) ;
		} else {
		    $term_so_far= " _proxy_jslib_assign('', $term_so_far, '$token', '$op', '')" ;
		}
		$new_last_token= ')' ;
		$div_ok= 1 ;
	    } elsif ($in=~ /\G$RE_JS_SKIP*(>>>=|<<=|>>=|[+*\/%&|^-]?=(?!=))/gco) {
		$op= $1 ;
		$new_val= (&proxify_js(&get_next_js_expr(\$in), 0, $with_level))[0] ;
		if ($term_so_far eq '') {
		    push(@out, ($with_level
				? " $token= _proxy_jslib_with_assign_rval(_proxy_jslib_with_objs, '', '$token', '$op', ($new_val), $token)"
				: " $token= _proxy_jslib_assign_rval('', '$token', '$op', ($new_val), (typeof $token=='undefined' ? void 0 : $token))") ) ;
		} else {
		    $term_so_far= " _proxy_jslib_assign('', $term_so_far, '$token', '$op', ($new_val))" ;
		}
		$new_last_token= ')' ;
		$div_ok= 0 ;
	    } else {
		# Pass object and name of property.  Only pass property's value
		#   if object is null, in which case it is needed for return
		#   value.
		if ($term_so_far eq '') {
		    $term_so_far= ($with_level
				   ? " _proxy_jslib_with_handle(_proxy_jslib_with_objs, '$token', $token, $next_is_paren, $in_new_statement)"
				   : " _proxy_jslib_handle(null, '$token', $token, $next_is_paren, $in_new_statement)" ) ;
		} else {
		    $term_so_far= " _proxy_jslib_handle($term_so_far, '$token', '', $next_is_paren, $in_new_statement)" ;
		}
		$new_last_token= ')' ;
		$div_ok= 1 ;
	    }


	# These eight arrays of the document object must have all subscripts
	#   incremented by the number of each type of element in the inserted
	#   HTML, so that the subscripts still refer to the intended page
	#   elements.
	# Here we assume the referring object is a document and don't check.
	# Also, it may refer to other documents' elements, but those also
	#   will probably need their subscripts incremented, so it's OK.
	# This is normally only needed for sloppy JS.  Better HTML/JS uses named
	#   elements, but some pages just use integer subscripts.
	# This errs when a non-numeric subscript is used that evaluates to a
	#   number.  It doesn't open a privacy hole.  If needed, we can revisit
	#   this.
	} elsif ($token eq 'applets' or $token eq 'embeds' or $token eq 'forms'
		 or $token eq 'ids' or $token eq 'layers' or $token eq 'anchors'
		 or $token eq 'images' or $token eq 'links')
	{
	    if ($doing_insert_here and $term_so_far ne '' and $in=~ /\G($RE_JS_SKIP*\[)/gco) {
		$skip1= $1 ;
		$next_expr= &get_next_js_expr(\$in,1) ;
		if ($next_expr=~ /^\s*\d+\s*$/) {
		    $term_so_far.= $token . $skip1 . "_proxy_jslib_increments['$token']+(" . (&proxify_js($next_expr, 0, $with_level))[0] . ')]' ;
		} else {
		    $term_so_far.= $token . $skip1 . '(' . (&proxify_js($next_expr, 0, $with_level))[0] . ')]' ;
		}
		last unless $in=~ /\G\]/gc ;
		$new_last_token= ']' ;
	    } else {
		$term_so_far.= $token ;
	    }
	    $div_ok= 1 ;


	# These reserved words must have their following parenthesized
	#   expression read, or else it could be confused with the start of a
	#   term.  "catch" and "function" also use parentheses, but those are
	#   argument lists and shouldn't be proxified; they're handled below.
	#   "with" blocks are more problematic and are also handled below.
	# Perl has a bug handling $1 in the "last unless..." and "push(...)"
	#   line below, so instead of using $1 for the push(), we save it to
	#   $paren.
	} elsif ($token eq 'if' or $token eq 'while' or $token eq 'for'
		 or $token eq 'switch')
	{
	    push(@out, $prefix, $term_so_far, $token) ;
	    $prefix= $term_so_far= '' ;
	    last unless $paren= $in=~ /\G($RE_JS_SKIP*\()/gco ;
	    $paren= $1 ;
	    push(@out, $paren, (&proxify_js(&get_next_js_expr(\$in,1), 0, $with_level))[0], ')') ;
	    last unless $in=~ /\G\)/gc ;
	    $div_ok= 0 ;

	# Parentheses after "catch" and "function" shouldn't be proxified.
	} elsif ($token eq 'catch') {
	    push(@out, $prefix, $term_so_far, $token) ;
	    $prefix= $term_so_far= '' ;
	    last unless $in=~ /\G($RE_JS_SKIP*\()/gco ;
	    $paren= $1 ;
	    push(@out, $paren, &get_next_js_expr(\$in,1), ')') ;
	    last unless $in=~ /\G\)/gc ;
	    $div_ok= 0 ;

	# Contrary to the spec, MSIE allows function identifiers to be object
	#   properties in dot notation, so allow "identifier(.identifier)*" .
	} elsif ($token eq 'function') {
	    push(@out, $prefix, $term_so_far, $token) ;
	    $prefix= $term_so_far= '' ;
	    #last unless $in=~ /\G($RE_JS_SKIP*)($RE_JS_IDENTIFIER_NAME)?($RE_JS_SKIP*\()/gco ;   # by the spec
	    last unless $in=~ /\G($RE_JS_SKIP*)($RE_JS_IDENTIFIER_NAME(?:\.(?:$RE_JS_IDENTIFIER_NAME))*)?($RE_JS_SKIP*\()/gco ;
	    ($skip1, $funcname, $skip2)= ($1, $2, $3) ;
	    # Update function name if it's from another proxy's library.
	    $funcname=~ s/^_proxy(\d*)_/'_proxy'.($1+1).'_'/e ;
	    push(@out, $skip1, $funcname, $skip2, &get_next_js_expr(\$in,1), ') {') ;
	    last unless $in=~ /\G\)$RE_JS_SKIP*\{/gc ;
	    $in_braces++ ;
	    $in_func= 1 ;
	    $div_ok= 0 ;

	# Supporting the deprecated with() statement is messy.  It requires
	#   maintaining a list of "with objects" in _proxy_jslib_with_objs; each
	#   with() statement appends its object to the end of that array, then
	#   truncates the array when it's done.  That _proxy_jslib_with_objs is
	#   declared and initialized if needed before the outermost with()
	#   statement.  Additionally, we must surround it all with "{}" in
	#   case it's in e.g. an if/else statement.
	# Putting that all together means we change "with (with_obj) code" to:
	#   "{ var _proxy_jslib_with_objs= [] ;
	#      with (_proxy_jslib_with_objs[_proxy_jslib_with_objs.length]= ("
	#            . &proxify_js($with_obj, 0, $with_level) . ")) "
	#            . &proxify_js($code, 0, $with_level+1)
	#            . "_proxy_jslib_with_objs.length-- ;}"
	# Note that objects in proxy_jslib_with_objs increase in precedence,
	#   so that array is traversed backwards in the related JS routines
	#   _proxy_jslib_with_handle() and _proxy_jslib_with_assign_rval().
	} elsif ($token eq 'with') {
	    push(@out, $prefix, $term_so_far) ;
	    $prefix= $term_so_far= '' ;
	    last unless $in=~ /\G($RE_JS_SKIP*)\(/gco ;
	    $skip1= $1 ;
	    $with_obj= (&proxify_js(&get_next_js_expr(\$in, 1), 0, $with_level))[0] ;
	    last unless $in=~ /\G\)($RE_JS_SKIP*)/gco ;
	    $skip2= $1 ;
	    if ($in=~ /\G\{/gc) {
		$code= '{' . (&proxify_js(&get_next_js_expr(\$in, 1), 0, $with_level+1))[0] . '}' ;
		last unless $in=~ /\G\}/gc ;
	    } else {
		# Note that a bare with() statement could still contain commas.
		$code= (&proxify_js(&get_next_js_expr(\$in), 0, $with_level+1))[0] ;
		$code.= ',' . (&proxify_js(&get_next_js_expr(\$in), 0, $with_level+1))[0]
		    while $in=~ /\G,/gc ;
	    }
	    # Only initialize _proxy_jslib_with_objs at first with().
	    push(@out, '{', ($with_level  ? ''  : 'var _proxy_jslib_with_objs= [] ;'),
		       "with$skip1(_proxy_jslib_with_objs[_proxy_jslib_with_objs.length]= ($with_obj))$skip2$code",
		       '; _proxy_jslib_with_objs.length-- ;}') ;
	    $div_ok= 0 ;



	# Handle "var" specially to avoid failing on e.g. "var open= 1 ;" .
	# "var ... in ..." clauses are handled by matching either "=" or "in"
	#   after the identifier name.
	} elsif ($token eq 'var' or $token eq 'let') {
	    push(@out, $prefix, $term_so_far, $token) ;
	    $prefix= $term_so_far= '' ;
	    while (1) {
		$var_decl= &get_next_js_expr(\$in,0) ;
		( ($skip1, $var, $eq, $value)= $var_decl=~ /^($RE_JS_SKIP*)($RE_JS_IDENTIFIER_NAME$RE_JS_SKIP*)(=|in)?(.*)$/s )
		    || last OUTER ;
		# Update variable name if it's from another proxy's library.
		$var=~ s/^_proxy(\d*)_/'_proxy'.($1+1).'_'/e ;
		push(@out, $skip1, $var) ;
		push(@out, $eq, (&proxify_js($value, 0, $with_level))[0]) if $eq ne '' ;
		last unless $in=~ /\G,/gc ;
		push(@out, ',') ;
	    }
	    $div_ok= 0 ;


	# "new" needs special handling because its expression may be
	#   treated differently than normal expressions, regarding parentheses
	#   and what the object is that "new" takes as its constructor-- it
	#   seems to take the leading part of the expression *without* the
	#   parentheses and argument list.  This causes problems with our
	#   transformation to "_proxy_jslib_handle()" etc., so put the
	#   constructor expression inside parentheses to tell "new" exactly
	#   what to use for it.
	} elsif ($token eq 'new') {
	    push(@out, $prefix, $term_so_far) ;
	    $prefix= $term_so_far= '' ;
	    my($pos)= pos($in) ;

	    # Handle "new Function(...)", which contains JS code.
	    # This will matter extremely rarely, and is a messy fix, but if not
	    #   handled is a privacy hole.
	    if ($in=~ /\G$RE_JS_SKIP*(?:(?:window\.)?Function\b|\((?:window\.)?Function\b\))/gco) {
		push(@out, '_proxy_jslib_new_function') ;
		# teeny bug-- should also push parens if $in is missing them

	    # Make exception for "new function() {...}" .
	    } elsif ($in=~ /\G($RE_JS_SKIP*function\s*\()/gco) {
		$term_so_far= 'new' . $1 ;
		my($args)= &get_next_js_expr(\$in, 1) ;
		last unless $in=~ /\G(\)$RE_JS_SKIP*\{)/gco ;
		$term_so_far.= $args . $1 ;
		my($body)= &proxify_js(&get_next_js_expr(\$in, 1), 0, $with_level, 0) ;
		last unless $in=~ /\G\}/gc ;
		$term_so_far.= $body . '}' ;
		$new_last_token= '}' ;
		$div_ok= 1 ;

	    # If it's an Audio, EventSource, WebSocket, or Worker object being constructed, proxify
	    #   the first argument.  Messy.
	    } elsif ($in=~ /\G($RE_JS_SKIP*(['"]?)(Audio|EventSource|WebSocket|Worker)\b\s*\2)/gco) {
		my $otype= $3 ;
		my($arg1, $other_args, $remainder) ;
		if ($in=~ /\G$RE_JS_SKIP*\(/gco) {
		    ($arg1, $remainder)=
			&proxify_js(&get_next_js_expr(\$in), 0, $with_level, 1) ;
		    $other_args= &get_next_js_expr(\$in, 1) ;
		    pos($in)= $pos, last  unless $in=~ /\G\)/gc ;
		    if ($arg1 ne '') {
			$term_so_far= "new $otype(_proxy_jslib_full_url($arg1) $other_args)" ;
		    } else {
			$term_so_far= "new $otype()" ;
		    }
		} else {
		    $term_so_far= "new $otype()" ;
		}
		$new_last_token= ')' ;
		$div_ok= 1 ;


	    # Otherwise, get expression up to "(" and put it in parentheses,
	    #   but no parentheses if expression is already surrounded by them.
	    } else {
		my($new_expr, $remainder) ;
		if ($in=~ /\G$RE_JS_SKIP*\(/gco) {
		    ($new_expr, $remainder)=
			&proxify_js(&get_next_js_expr(\$in, 1), 0, $with_level, 1) ;
		    pos($in)= $pos, last  unless $in=~ /\G\)/gc ;
		} else {
		    ($new_expr, $remainder)=
			&proxify_js(&get_next_js_constructor(\$in), 0, $with_level, 1) ;
		}
		pos($in)= $pos, last  if $remainder ne '' ;

		$term_so_far.= "new ($new_expr)" ;
		$new_last_token= ')' ;
		$div_ok= 1 ;
	    }


	# Only bother with this if call to _proxy_jslib_write_buffers() must
	#   be inserted, i.e. if $top_level.
	} elsif (($token eq 'return') and !$in_func and $top_level) {
	    push(@out, $prefix, $term_so_far) ;
	    $prefix= $term_so_far= '' ;
	    $needs_jslib= 1 ;
	    # Allow commas, but not semicolons; perhaps $allow_multiple in
	    #   get_next_js_expr() should be 3-way.
	    $expr= &get_next_js_expr(\$in,0) ;
	    $expr.= ', ' . &get_next_js_expr(\$in,0) while $in=~ /\G$RE_JS_SKIP*,$RE_JS_SKIP*/gco ;
	    $expr= (&proxify_js($expr, 0, $with_level))[0] ;
	    $expr= 'void 0' if $expr eq '' ;
	    push(@out,
		 "return ((_proxy_jslib_ret= ($expr)), _proxy_jslib_flush_write_buffers(), _proxy_jslib_ret)") ;
	    $div_ok= 0 ;


	# This is all reserved words except "this", "super", "true", "false",
	#   and "null", which may be part of an object expression.  (Also
	#   missing are the nine reserved words handled directly above.)
	#} elsif ($RE_JS_SET_RESERVED_WORDS_NON_EXPRESSION{$token}) {
	} elsif ($token=~ /^(?:abstract|boolean|break|byte|case|char|class|const|continue|debugger|default|delete|do|else|enum|export|extends|final|finally|float|goto|implements|in|instanceof|int|interface|long|native|package|private|protected|return|short|static|synchronized|throw|throws|transient|try|typeof|void|volatile)$/) {
	    push(@out, $prefix, $term_so_far, $token) ;
	    $prefix= $term_so_far= '' ;
	    $div_ok= 0 ;


	# This handles identifiers and a certain few reserved words, above.
	# Most reserved words must be handled separately from identifiers, or
	#   else there may be syntatic ambiguities, e.g. "if (foo) (...)".
	} elsif ($token=~ /^$RE_JS_IDENTIFIER_NAME$/o) {
	    # Handle automatic semicolon insertion.  For more notes about
	    #   automatic semicolon insertion, see comments in
	    #   get_next_js_expr() below.
	    if ($newline_since_last_token
		and $last_token=~ m#^(?:\)|\]|\+\+|--)$|
				    ^(?!(?:case|delete|do|else|in|instanceof|new|typeof|void|function|var)$)
				     (?:\pL|[\$_\\0-9'"]|\.\d|/..)#x )
	    {
		push(@out, $prefix, $term_so_far) ;
		$prefix= '' ;
		$term_so_far= $token ;
	    } else {
		$term_so_far.= $token ;
	    }
	    $div_ok= 1 ;


	} elsif ($token eq '.') {
	    $term_so_far.= '.' ;
	    $div_ok= 0 ;


	# For "(", get inside parens, proxify, and add to output.
	} elsif ($token eq '(') {
	    $does_write= 1 ;   # any function call could do a write()
	    $term_so_far.= '(' . (&proxify_js(&get_next_js_expr(\$in,1), 0, $with_level))[0] . ')' ;
	    last unless $in=~ /\G\)/gc ;
	    $new_last_token= ')' ;
	    $div_ok= 1 ;


	# For "[", get inside brackets, proxify, and pass parenthesized as
	#   second parameter to _proxy_jslib_handle().  Or, start new term
	#   if it looks like an array literal instead.
	} elsif ($token eq '[') {
	    # Don't change it for simple integer subscripts.
	    if ($in=~ /\G($RE_JS_SKIP*\d+$RE_JS_SKIP*\])/gco) {
		$term_so_far.= '[' . $1 ;
		$new_last_token= ']' ;
		$div_ok= 1 ;
	    } else {
		$sub_expr= (&proxify_js(&get_next_js_expr(\$in,1), 0, $with_level))[0] ;
		last unless $in=~ /\G\]/gc ;

		# Peek ahead to see if the next token is an open parenthesis
		my $old_pos= pos($in) ;
		my $next_is_paren= $in=~ /\G$RE_JS_SKIP*\(/gco  ? 1  : 0 ;
		pos($in)= $old_pos ;

		if ($term_so_far ne '') {
		    $needs_jslib= 1 ;
		    $new_last_token= ')' ;
		    if ($prefix ne '') {
			$term_so_far= " _proxy_jslib_assign('$prefix', $term_so_far, ($sub_expr), '', '')" ;
			$prefix= '' ;
			$div_ok= 0 ;
		    } elsif ($in=~ /\G$RE_JS_SKIP_NO_LT*(\+\+|--)/gco) {
			$op= $1 ;
			$term_so_far= " _proxy_jslib_assign('', $term_so_far, ($sub_expr), '$op', '')" ;
			$div_ok= 1 ;
		    } elsif ($in=~ /\G$RE_JS_SKIP*(>>>=|<<=|>>=|[+*\/%&|^-]?=(?!=))/gco) {
			$op= $1 ;
			$new_val= (&proxify_js(&get_next_js_expr(\$in), 0, $with_level))[0] ;
			$term_so_far= " _proxy_jslib_assign('', $term_so_far, ($sub_expr), '$op', ($new_val))" ;
			$div_ok= 0 ;
		    } else {
			$term_so_far= " _proxy_jslib_handle($term_so_far, ($sub_expr), '', $next_is_paren, $in_new_statement)" ;
			$div_ok= 1 ;
		    }
		} else {
		    $term_so_far= "[$sub_expr]" ;
		    $new_last_token= ']' ;
		    $div_ok= 1 ;
		}
	    }


	# For "{", if it looks like an object literal, start new term.  How do
	#   we distinguish {foo:bar} between an object literal and a block starting
	#   with a label?  Guess:  If the previous token was a punctuator but
	#   not ")", or was one of these keywords, or if there's no previous
	#   token, then assume it's an object literal.  Not perfect.
	} elsif ($token eq '{' and $term_so_far eq '' 
		 and (!defined $last_token or $last_token=~ /^(?!\))$RE_JS_PUNCTUATOR$/o
		      or $last_token=~ /^(?:case|delete|in|instanceof|new|return|throw|typeof)$/)
		 and $in=~ /\G($RE_JS_SKIP*((?:$RE_JS_IDENTIFIER_NAME|$RE_JS_STRING_LITERAL|$RE_JS_NUMERIC_LITERAL)$RE_JS_SKIP*:|\}))/gco)
	{
	    $term_so_far= '{' ;
	    if ($2 ne '}') {
		$term_so_far.= $1 ;
		$term_so_far.= (&proxify_js(&get_next_js_expr(\$in, 0), 0, $with_level))[0] ;
		while ($in=~ /\G,/gc) {
		    $term_so_far.= ',' ;
		    # Illegal, but some sites end object literal with extra ",".
		    last if $in=~ /\G(?=$RE_JS_SKIP*\})/gco ;
		    last OUTER unless $in=~ /\G($RE_JS_SKIP*(?:$RE_JS_IDENTIFIER_NAME|$RE_JS_STRING_LITERAL|$RE_JS_NUMERIC_LITERAL)$RE_JS_SKIP*:)/gco ;
		    $term_so_far.= $1 ;
		    $term_so_far.= (&proxify_js(&get_next_js_expr(\$in, 0), 0, $with_level))[0] ;
		}
		last unless $in=~ /\G$RE_JS_SKIP*\}/gc ;
	    }

	    $term_so_far.= $new_last_token= '}' ;
	    $div_ok= 1 ;


	# All other punctuators end a term.
	#} elsif ($RE_JS_SET_ALL_PUNCTUATORS{$token}) {
	} elsif ($token=~ /^(?:$RE_JS_PUNCTUATOR|$RE_JS_DIV_PUNCTUATOR)$/o) {
	    push(@out, $prefix, $term_so_far, $token) ;
	    $prefix= $term_so_far= '' ;
	    $div_ok= ($token eq ')' or $token eq ']' or $token eq '}') ;

	} else {
	    &HTMLdie("Shouldn't get here, token= [$token]") ;
	}

	if (defined($token)) {
	    $last_token= $new_last_token ne ''  ? $new_last_token  : $token ;
	    $newline_since_last_token= 0 ;
	}
    }

    push(@out, $prefix, $term_so_far) ;

    # If there's been a write or writeln, then insert a call to flush the
    #   output buffer.  A similar call is inserted into every appropriate
    #   "return" statement; see handling of that above.
    push(@out, " ;\n_proxy_jslib_flush_write_buffers() ;"), $needs_jslib= 1
	if $top_level && $does_write ;


#&HTMLdie("remainder=[".substr($in, pos($in)).']') if pos($in)!=length($in) ;

    # Return proxified $in, and the remainder of $in that couldn't be proxified.
    return ( join('', @out), substr($in, pos($in)) ) ;
}



# Given a pointer to a string, return the longest complete JavaScript expression
#   starting at the string match pointer (pos), and update that string pointer.
# If $allow_multiple is set, then read multiple expressions/statements as
#   possible, only ending on an unmatched closing parenthesis (or error).
#   Otherwise, also end on a top-level comma or semicolon.
# We handle a special case here, where we're parsing a "new" statement, as
#   indicated by $is_new.  In this case, we don't include an argument list in
#   the returned expression, to match what "new" takes as its constructor.
# The method here is to read in one token at a time, and compare it to various
#   possible tokens that could end the expression.  For this to work, we need
#   to keep a stack of various parenthesis characters which may nest; the
#   expression may only end when the parenthesis stack is empty.  Note that
#   the "?:" characters are treated like parentheses, to handle conditional
#   expressions.  The ":" needs special treatment, because it may also be used
#   in switch statements, labelled statements, and object literals.
# In this routine, all opening parentheses "([{" are treated the same; likewise
#   for all closing parentheses ")]}".  This is a shortcut that works for all
#   valid JavaScript, but errs on e.g. "( { ) }".  A browser wouldn't run that
#   anyway, so this shortcut seems safe.
# This routine is inefficient in that it tokenizes the JavaScript but doesn't
#   save that effort, thus the expression will require tokenizing again later.
#   This could be avoided if we had a good way of matching sequences of tokens
#   (a la regexes) in proxify_js().
sub get_next_js_expr {
    my($s, $allow_multiple, $is_new)= @_ ;
    my(@out, @p, $element, $token, $div_ok, $last_token, $pos, $expr_block_state,
       $closequote1, $closequote2, $conditional_state, $conditional_stack_size) ;

    while (1) {

	# Note that these patterns contain an embedded set of parentheses that
	#   only match if the input element is a token.
	# Correction:  Because of Perl's long-string-literal bug, there are two
	#   additional sets of embedded parentheses, which may match /'/ or /"/ .
	last unless ($div_ok
		     ? $$s=~ /\G($RE_JS_INPUT_ELEMENT_DIV)/gco
		     : $$s=~ /\G($RE_JS_INPUT_ELEMENT_REG_EXP)/gco) ;

	($element, $token, $closequote1, $closequote2)= ($1, $2, $3, $4) ;

	# To work around Perl's long-string-literal bug, read in rest of
	#   string literal if needed.
	if ($token=~ /^['"]/ && !$closequote1 && !$closequote2) {
	    last unless &get_string_literal_remainder($s, \$token) ;
	    $element= $token ;
	}


	# Track state of expression block so far, needed for handling automatic
	#   semicolon insertion (only relevant when not $allow_multiple).
	# Possible values for $expr_block_state:
	#     0 -- before main expression block
	#     1 -- "function" encountered, block not started
	#     2 -- inside main expression block (function block or object literal)
	#     3 -- after expression block
	$expr_block_state= 1  if !$allow_multiple and !@p and $element eq 'function' ;

	# If $element is either ";" or "," , then end the expression if the
	#   parenthesis stack is empty.  Otherwise, continue.
	if ($element eq ';' or $element eq ',') {
	    pos($$s)-= 1, return join('', @out)  if !$allow_multiple and !@p ;

	# If it's a line terminator, then handle automatic semicolon insertion:
	#   if not allowing multiple statements, if the parenthesis stack is
	#   empty, if the previous token is not acceptable before an identifier
	#   or keyword, and if the next input is an identifier or keyword, then
	#   act as if a semicolon had been encountered, similar to above.
	# I'm not sure this is rigorous, but it should work for virtually all
	#   real-life situations.  Let me know if you find any privacy holes,
	#   or any actual sites it doesn't work with.
	# Testing the next input for an identifier requires saving and restoring
	#   pos($$s).
	# Tokens "not acceptable before an identifier or keyword" are identifiers
	#   and most keywords, numeric/string/regex literals, and the punctuators
	#   ")", "]", "++", and "--".  As it turns out, this is much the same
	#   regex as used in the setting of $div_ok above and below; the only
	#   difference is four keywords.
	# For more details, see the ECMAScript spec, section 7.9 .
	} elsif ($element=~ /^$RE_JS_LINE_TERMINATOR$/o) {
	    if (!$allow_multiple and !@p) {
		$pos= pos($$s) ;
		pos($$s)= $pos-length($element), return join('', @out)
		    if $last_token=~ m#^(?:\)|\]|\+\+|--)$|
				       ^(?!(?:case|delete|do|else|in|instanceof|new|typeof|void|function|var)$)
					(?:\pL|[\$_\\0-9'"]|\.\d|/..)#x
			and $$s=~ /\G$RE_JS_SKIP*$RE_JS_IDENTIFIER_NAME/gco ;

		# Also end on inserted semicolon if just finished a {} block that's an
		#   expression, like a function expression or an object literal, and if
		#   the following token is not acceptable after such an expression.
		# Tokens acceptable after a noun-like block include all punctuators
		#   except "{", and the keyword "instanceof" (not that all of those make
		#   sense).  Be sure not to consume the matching token, by using "(?=...)" .
		pos($$s)= $pos-length($element), return join('', @out)
		    if $expr_block_state==3
		       and $$s!~ /\G$RE_JS_SKIP*(?!\{)(?=$RE_JS_PUNCTUATOR|instanceof)/gco ;
	    }


	# If $element is an opening "parenthesis" (including "?"), then push it
	#   onto the parenthesis stack and continue.
	} elsif ($element=~ /^[(\[\{\?]$/) {
	    # If we're parsing a "new" statement, then break on top-level "(".
	    pos($$s) -= 1, return join( '', @out )
		if $is_new and !@p and $element eq '(' ;

	    $conditional_state= 2  if $conditional_state==1 and $element eq '(' ;

	    # For "{", if it's either a function start or an object literal,
	    #   then set $expr_block_state=2 .
	    if (!$allow_multiple and !@p and $element eq '{') {
		$pos= pos($$s) ;
		$expr_block_state= 2
		   if $expr_block_state==1
		      or $$s=~ /\G$RE_JS_SKIP*((?:$RE_JS_IDENTIFIER_NAME|$RE_JS_STRING_LITERAL|$RE_JS_NUMERIC_LITERAL)$RE_JS_SKIP*:|\})/gco ;
		pos($$s)= $pos ;
	    }

	    push(@p, $element) ;


	# If $element is a closing "parenthesis" (including ":"), then end the
	#   expression if the parenthesis stack is empty.  Otherwise, pop the
	#   parenthesis stack and continue.
	# If $element is ":", then only pop the parenthesis stack if the top
	#   item is a "?".  This prevents popping when the ":" is not part of
	#   a "?"...":" conditional (like in a switch statement, labelled
	#   statement, or object literal).  This is why we store the stack
	#   instead of using a simple counter.
	} elsif ($element=~ /^[)\]}:]$/) {
	    pos($$s)-= 1, return join('', @out)  unless @p ;
	    pop(@p)  unless ($element eq ':' and $p[$#p] ne '?') ;

	    $conditional_state= 3  if $conditional_state==2 and $element eq ')' and @p==$conditional_stack_size ;

	    # Update $expr_block_state if we just closed an expression block.
	    $expr_block_state= 3  if !$allow_multiple and !@p and $element eq '}' and $expr_block_state==2 ;


	} elsif ($element eq 'if' or $element eq 'while' or $element eq 'for' or $element eq 'switch') {
	    $conditional_state= 1 ;
	    $conditional_stack_size= @p ;
	}


	# Whatever we got, add it to the output.
	push(@out, $element) ;

	# If a token was gotten, then set $div_ok according to the token.
	# See the comments in proxify_js() for details.
	if (defined($token)) {
	    $div_ok= $token=~ m#^(?:\)|\]|\}|\+\+|--)$|
				^(?!(?:case|delete|do|else|in|instanceof|new|return|throw|typeof|void)$)
				 (?:\pL|[\$_\\0-9'"]|\.\d|/..)#x ;
	    $div_ok= 0, $conditional_state= 0 if $conditional_state==3 ;
	    $last_token= $token ;
	}
    }

    # If we got here, then $$s has no more tokens.  Either there's a syntax
    #   error, or the end of the string has been reached.  We'll *guess* that
    #   we have a valid expression if the parenthesis stack is empty, and
    #   return it; otherwise, return undef.  Either way, the pos($$s) doesn't
    #   change.
    return  @p  ? undef  : join('', @out) ;
}



# Given a reference to a string, return the next JavaScript term in it, split
#   up into the leading object and the final property (either the entire
#   contents between "[]" or a quoted identifier).  The string search pointer
#   is correctly updated.
# On error, return undef.
# Note that if $o is empty, then $p is guaranteed to be a quoted identifier.
sub get_next_js_term {
    my($s)= @_ ;
    my($o, $p, $ofrag) ;

    $$s=~ /\G$RE_JS_SKIP*($RE_JS_IDENTIFIER_NAME|[\[\{\(])/gco or return ;
    if ($1 eq '[') {
	# read array literal
	$ofrag= '[' . &get_next_js_expr($s, 1) . ']';
	$$s=~ /\G\]/gco  or return undef ;
    } elsif ($1 eq '{') {
	# read object literal
	$ofrag= '{' . &get_next_js_expr($s, 1) . '}';
	$$s=~ /\G\}/gco  or return undef ;
    } elsif ($1 eq '(') {
	# read parenthesized expression
	$ofrag= '(' . &get_next_js_expr($s, 1) . ')';
	$$s=~ /\G\)/gco  or return undef ;
    } else {
	$p= "'$1'" ;
	$ofrag= $1 ;
    }

    while ($$s=~ /\G$RE_JS_SKIP*([.\[\(])/gco) {
	$o.= $ofrag ;
	if ($1 eq '.') {
	    $$s=~ /\G$RE_JS_SKIP*($RE_JS_IDENTIFIER_NAME)/gco  or return ;
	    $p= "'$1'" ;
	    $ofrag= '.' . $1 ;
	} elsif ($1 eq '[') {
	    $p= &get_next_js_expr($s, 1) ;
	    $ofrag= "[$p]" ;
	    $$s=~ /\G\]/gco  or return undef ;
	} elsif ($1 eq '(') {
	    $p= '' ;
	    $ofrag= '(' . &get_next_js_expr($s, 1) . ')' ;
	    $$s=~ /\G\)/gco  or return undef ;
	}
    }

    return ($o, $p) ;
}


# Given a reference to a string, return the next JavaScript constructor in it,
#   to be used in a "new" statement.  Basically, this is the leading part of
#   a term before the first "(".  See comments in proxify_js(), where the
#   "new" token is handled.
# This currently doesn't handle an array literal starting the term....
sub get_next_js_constructor {
    my($s)= @_ ;

    $$s=~ /\G$RE_JS_SKIP*($RE_JS_IDENTIFIER_NAME|$RE_JS_STRING_LITERAL_START)/gco ;
    my($c, $closequote1, $closequote2)= ($1, $2, $3) ;

    # To work around Perl's long-string-literal bug, read in rest of
    #   string literal if needed.
    if ($c=~ /^['"]/ && !$closequote1 && !$closequote2) {
	return unless &get_string_literal_remainder($s, \$c) ;
    }

    while ($$s=~ /\G$RE_JS_SKIP*([.\[])/gco) {
	if ($1 eq '.') {
	    $$s=~ /\G$RE_JS_SKIP*($RE_JS_IDENTIFIER_NAME)/gco or return ;
	    $c.= ".$1" ;
	} elsif ($1 eq '[') {
	    $c.= '[' . &get_next_js_expr($s, 1) . ']' ;
	    $$s=~ /\G\]/gco or return ;
	}
    }

    return $c ;
}


# Given a string of JavaScript code, break it into a list of tokens.  Well,
#   elements actually, since it includes whitespace and comments.
# Returns the resulting list.
# Would be more efficient to return a reference to @ret.
# jsm-- this has bug tokenizing "if (expr) /foo/", since $div_ok is wrongly
#   true after the ")".
sub tokenize_js {
    my($in)= @_ ;
    my(@ret, $div_ok, $element, $token, $closequote1, $closequote2);

    while ($div_ok  ? $in=~ /\G($RE_JS_INPUT_ELEMENT_DIV)/gco
		    : $in=~ /\G($RE_JS_INPUT_ELEMENT_REG_EXP)/gco) {

	($element, $token, $closequote1, $closequote2)= ($1, $2, $3, $4) ;

	# To work around Perl's long-string-literal bug, read in rest of
	#   string literal if needed.
	if (defined $token && $token=~ /^['"]/ && !$closequote1 && !$closequote2) {
	    last unless &get_string_literal_remainder(\$in, \$token) ;
	    $element= $token ;
	}

	push(@ret, $element);

	if (defined($token)) {
	    $div_ok= $token=~ m#^(?:\)|\]|\+\+|--)$|
				^(?!(?:case|delete|do|else|in|instanceof|new|return|throw|typeof|void)$)
				 (?:\pL|[\$_\\0-9'"]|\.\d|/..)#x ;
	}
    }

    return @ret;
}



# Given two string pointers, this reads the remainder of a string literal
#   from the first string onto the end of the second string.
# Returns true if string is successfully read, or else throws an
#   "end_of_input\n" error (to be caught by calling eval{} block).
# This is needed to work around Perl's long-string-literal bug, as well as
#   when "</script" is in a JS literal string.
sub get_string_literal_remainder {
    my($inp, $startp)= @_ ;
    my($q)= substr($$startp, 0, 1) ;
    my $RE= ($q eq "'")  ? $RE_JS_STRING_REMAINDER_1  : $RE_JS_STRING_REMAINDER_2 ;
    while ($$inp=~ /\G($RE)/gc) {
	last if $1 eq '' and $2 eq '' ;
	$$startp.= $1 ;
	return 1 if $2 ;
    }
    die "end_of_input\n" ;   # throw error if regex failed.
}



# Given a string of JS code, splits off the last statement from it and returns
#   [ all_but_last_statement, last_statement ] .  This is required to support
#   "javascript:" URLs and their return values correctly.
# Note that the input value $s is a reference to a string, not a string.
sub separate_last_js_statement {
    my($s)= @_ ;
    my($e, $rest, $last) ;

    while (($e= &get_next_js_expr($s)) or (pos($$s)!=length($$s))) {
	return ($rest, $last.$e)
	    if $$s=~ /\G(?:;|$RE_JS_LINE_TERMINATOR|$RE_JS_SKIP)*\z/gco ;
	if ($$s=~ /\G(?:;|$RE_JS_LINE_TERMINATOR)/gco) {
	    $rest.= $last . $e . ';' ;
	    $last= '' ;
	} else {
	    return ($rest, $last)  if $e eq '' ;   # probably a syntax error
	    $last.= $e ;
	    $last.= ','  if $$s=~ /\G,/gco ;
	}
    }
    return ($rest, $last) ;
}



# Set the various regular expressions used in parsing JavaScript.
# These regular expressions are taken directly from the "productions" (rules of
#   grammar) of the ECMAScript specification, which is basically the JavaScript
#   spec.  The spec version followed below is the standard ECMA-262, published
#   in December 1999.  It's available at http://www.ecma.ch/ecma1/STAND/ECMA-262.HTM .
# For the most part, these patterns represent the grammar as strictly defined
#   in the ECMAScript spec.  For example, StringLiteral doesn't match '"\x"' or
#   '"\012"' and the pattern here reflects that, though other implementations
#   may be more permissive.  If needed, we can extend the patterns later to
#   cover common misuses.  Also, if we decide to support octal numeric literals
#   and octal escape sequences (as older implementations did), appendix B.1 of
#   the spec has the details.  In any case, when this program scans script
#   content and at some point fails to match a valid input element, it discards
#   the remainder of the script.  Thus, while the strictness may prevent sloppy
#   scripts from running, it gives maximum protection from privacy holes, etc.
# Some of the patterns here do not strictly follow the spec, for purposes of
#   multi-platform compatibility or performance.  To my knowledge, they work
#   fine for actual existing pages (as opposed to hypothetical cases), and they
#   do not open any privacy holes.  If you find otherwise, please let me know!
#   The various strictly conformant patterns are collected in comments at the
#   end of this routine.  Several have to do with the Unicode line terminators
#   \x{2028} and \x{2029}, which we ignore in the patterns here.
# We're not using the \x{unicode} construct, because it's not fully supported
#   yet, e.g. in character classes.
# Patterns use no-backtracking (the "(?>...)" construct) where possible for
#   speed; also, in some cases it prevents splitting tokens inappropriately.
#   No-backtracking patterns work here because the parsing and tokenizing is
#   pretty deterministic (i.e. unambiguous context of each input, which means
#   no backtracking is needed when parsing).  If we go with a more top-down
#   non-deterministic approach, we'd probably use fewer if any no-backtracking
#   patterns (though we'd still need to prevent splitting tokens).
# When these patterns are used elsewhere, don't forget they're no-backtracking!
sub set_RE_JS {

    # If we decide to support UTF-8, this allows multi-platform compatibility.
    #eval '/\x{2028}/' ;
    #my($utf8_OK)=  $@ eq '' ;


    $RE_JS_WHITE_SPACE= qr/[\x09\x0b\x0c \xa0]|\p{Zs}/ ;
    $RE_JS_LINE_TERMINATOR= qr/[\012\015]/ ;


    # Note that a single-line comment must not have a backtracking pattern, to
    #   force it to grab all characters up to a line terminator; multi-line
    #   comment must not backtrack either, to prevent it from grabbing beyond
    #   the first "*/".  So entire pattern is enclosed in (?>...) .
    # Technically, a "/*...*/" -style comment that contains a line terminator
    #   should be replaced by a line terminator during parsing, rather than
    #   be discarded entirely.  This may become relevant in the future if we
    #   parse syntax more rigorously, handle automatic semicolon insertion, etc.
    # Browsers also treat "<!--" as starting a one-line comment, so authors can
    #   use the old trick of an HTML comment to hide JS from non-JS browsers.
    #   This recognition of "<!--" is not part of the JS spec, but we handle
    #   it here.
    $RE_JS_COMMENT= qr#(?>/\*.*?\*/|//[^\012\015]*|<!--[^\012\015]*)#s ;


    # UnicodeLetter can be Unicode categories/properties of
    #   (Lu, Ll, Lt, Lm, Lo, Nl).  This can be condensed to (L, Nl).  Also,
    #   Nl doesn't seem to exist in Perl 5.6.0.  Thus, for now, use "\pL" to
    #   check for any letter.  Note that the "\pL" construct can't be used
    #   in character classes.
    # "\p{Pc}" doesn't exist in Perl 5.6.0.  So, don't use it either.
    # Eventually, we could set different values based on the Perl version, if
    #   there's demand.
    # jsm-- see if Perl 5.8.x lets us do this right.
    $RE_JS_IDENTIFIER_START= qr/\pL|[\$_]|\\u[0-9a-fA-F]{4}/ ;
    $RE_JS_IDENTIFIER_PART=  qr/$RE_JS_IDENTIFIER_START|\p{Mn}|\p{Mc}|\p{Nd}/ ;
    $RE_JS_IDENTIFIER_NAME=  qr/(?>$RE_JS_IDENTIFIER_START$RE_JS_IDENTIFIER_PART*)/ ;


    # Put the longest punctuators first in the list of alternatives.
    $RE_JS_PUNCTUATOR= qr/(?>>>>=?|===|!==|<<=|>>=|[<>=!+*%&|^-]=|\+\+|--|<<|>>|&&|\|\||[{}()[\].;,<>+*%&|^!~?:=-])/ ;
    $RE_JS_DIV_PUNCTUATOR= qr!(?>/=?)! ;


    # Hex literal must come before decimal, so that "0x..." is not parsed as "0"
    #   and a syntax error.  2nd and 3rd alternatives comprise DecimalLiteral
    #   plus the non-standard OctalIntegerLiteral, defined in section B.1 of the
    #   spec.
    $RE_JS_NUMERIC_LITERAL= qr/(?>0[xX][0-9a-fA-F]+|
				  [0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?|
				  \.[0-9]+(?:[eE][+-]?[0-9]+)?)
			       (?!$RE_JS_IDENTIFIER_START)
			      /x ;


    # The last alternative here represents CharacterEscapeSequence, fully expanded.
    # Note that this includes the non-standard OctalEscapeSequence, defined in
    #   section B.1 of the spec.
    # Unfortunately, some browsers allow a line terminator in the string if it's
    #   preceded by "\".  So, against the spec, allow line terminators in
    #   escape sequences.
    # Perl itself has a bug such that certain long strings crash with certain
    #   regular expressions.  Unfortunately, $RE_JS_STRING_LITERAL here is one
    #   of those regular expressions.  To work around it requires changes in
    #   a few places; here, we define $RE_STRING_LITERAL_START,
    #   $RE_STRING_REMAINDER_1, and $RE_STRING_REMAINDER_2 for the workaround.
    #   When comments elsewhere in the program refer to "Perl's long-string-literal
    #   bug", this is what that means.
    # Note that those three new patterns each have embedded parentheses that
    #   must be accommodated when used-- $RE_JS_STRING_START has two, and
    #   $RE_STRING_REMAINDER_1 and $RE_STRING_REMAINDER_2 each have one.
    #$RE_JS_ESCAPE_SEQUENCE= qr/x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|(?:[0-3]?[0-7](?![0-9])|[4-7][0-7]|[0-3][0-7][0-7])|[^0-9xu\012\015]/ ;
    $RE_JS_ESCAPE_SEQUENCE= qr/x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|(?:[0-3]?[0-7](?![0-9])|[4-7][0-7]|[0-3][0-7][0-7])|[^0-9xu]/ ;
    $RE_JS_STRING_LITERAL= qr/'(?>(?:[^'\\\012\015]|\\$RE_JS_ESCAPE_SEQUENCE)*)'|
			      "(?>(?:[^"\\\012\015]|\\$RE_JS_ESCAPE_SEQUENCE)*)"/x ;
    $RE_JS_STRING_LITERAL_START= qr/'(?>(?:[^'\\\012\015]|\\$RE_JS_ESCAPE_SEQUENCE){0,5000})('?)|
				    "(?>(?:[^"\\\012\015]|\\$RE_JS_ESCAPE_SEQUENCE){0,5000})("?)/x ;
    $RE_JS_STRING_REMAINDER_1= qr/(?>(?:[^'\\\012\015]|\\$RE_JS_ESCAPE_SEQUENCE){0,5000})('?)/ ;
    $RE_JS_STRING_REMAINDER_2= qr/(?>(?:[^"\\\012\015]|\\$RE_JS_ESCAPE_SEQUENCE){0,5000})("?)/ ;

    # ECMAScript 5 allows an unescaped "/" inside character classes, unlike ECMAScript 3.
    #$RE_JS_REGULAR_EXPRESSION_LITERAL= qr!/(?>(?:[^\012\015*\\/]|\\[^\012\015])
    #                                          (?:[^\012\015\\/]|\\[^\012\015])*)
    #                                      /(?>$RE_JS_IDENTIFIER_PART*)
    #                                     !x ;
    $RE_JS_REGULAR_EXPRESSION_LITERAL=
	qr!/(?>(?:[^\012\015*\\/[] | \[(?:[^\\\]\012\015]|\\[^\012\015])*\] | \\[^\012\015])
	       (?:[^\012\015\\/[]  | \[(?:[^\\\]\012\015]|\\[^\012\015])*\] | \\[^\012\015])*)
	   /(?>$RE_JS_IDENTIFIER_PART*)
	  !x ;


    # NumericLiteral should come before Punctuator, to avoid parsing e.g.
    #   ".4" as "." and "4".
    # Uses $RE_JS_STRING_LITERAL_START instead of $RE_JS_STRING_LITERAL to
    #   work around Perl's long-string-literal bug.
#    $RE_JS_TOKEN= qr/$RE_JS_IDENTIFIER_NAME|$RE_JS_NUMERIC_LITERAL|$RE_JS_PUNCTUATOR|$RE_JS_STRING_LITERAL/ ;
    $RE_JS_TOKEN= qr/$RE_JS_IDENTIFIER_NAME|$RE_JS_NUMERIC_LITERAL|$RE_JS_PUNCTUATOR|$RE_JS_STRING_LITERAL_START/ ;


    # JavaScript has a parsing quirk-- to handle the ambiguity that "/" may
    #   start either a division operator or a regular expression literal, it's
    #   specified that the parser should match a division operator if it's
    #   allowed by the higher-level grammar, and otherwise match a regular
    #   expression literal.  So it provides the two goal productions below.
    #   When we use them, we'll try to guess from the context which to use.
    # These patterns aren't strictly correct, because each has the extra
    #   alternative at the end to match in case we guess wrong.  Also, we
    #   combine consecutive WhiteSpace input elements here.
    # These patterns have a quirk/hack that is important to be aware of:
    #   there's a set of parentheses surrounding the final three alternatives,
    #   and any time either pattern is used it will generate an extra
    #   backreference, and a $1 (or $2, or whatever).  This lets us know if
    #   the input element matched was a token (here counting division operators
    #   and regular expression literals as tokens), which aids our process of
    #   guessing whether a division operator is allowed as the next input (see
    #   above):  we guess based on which token it is, or leave the current
    #   guess unchanged if it's not a token.
    # Correction:  Because of Perl's long-string-literal bug, these two patterns
    #   have two extra sets of parentheses inside $RE_JS_TOKEN.
    # Note that Comment has to come before DivPunctuator to correctly parse "//".

    $RE_JS_INPUT_ELEMENT_DIV= qr/(?>$RE_JS_WHITE_SPACE+)|$RE_JS_LINE_TERMINATOR|$RE_JS_COMMENT|
				 ($RE_JS_TOKEN|$RE_JS_DIV_PUNCTUATOR|$RE_JS_REGULAR_EXPRESSION_LITERAL)/x ;

    $RE_JS_INPUT_ELEMENT_REG_EXP= qr/(?>$RE_JS_WHITE_SPACE+)|$RE_JS_LINE_TERMINATOR|$RE_JS_COMMENT|
				     ($RE_JS_TOKEN|$RE_JS_REGULAR_EXPRESSION_LITERAL|$RE_JS_DIV_PUNCTUATOR)/x ;


    # These are pseudo-productions of those input elements that can come between
    #   tokens and are (pretty much) ignored.
    # Note that each represents one item and should normally be followed by "*".
    # $RE_JS_SKIP_NO_LT excludes line terminators for where those are not allowed.
    $RE_JS_SKIP= qr/(?>$RE_JS_WHITE_SPACE+)|$RE_JS_LINE_TERMINATOR|$RE_JS_COMMENT/ ;
    $RE_JS_SKIP_NO_LT= qr/(?>$RE_JS_WHITE_SPACE+)|$RE_JS_COMMENT/ ;



    #-------------------------------------------------------------------------
    #  various sets to test, rather than using long regexes in proxify_js()
    #-------------------------------------------------------------------------

    # Unfortunately, this doesn't help, based on performance testing, so it
    #   has been removed.
    # The idea is to set these hashes so that in proxify_js() we can merely
    #   test e.g. $RE_JS_SET_TRAPPED_PROPERTIES{$token} instead of using
    #   long regular expressions that are essentially lists of constant tokens.
    #   I would have thought this would be much faster, but it wasn't.
    # A similar mechanism was also tested in _proxy_jslib_proxify_js(), but
    #   it didn't help there either.  :(  It did, however, help significantly
    #   in a Java port of proxify_js().

    #my(@w)= qw(
    #    open write writeln close replace load eval
    #    setInterval setTimeout toString
    #    src href background lowsrc action location
    #    URL referrer baseURI
    #    useMap longDesc cite codeBase profile
    #    cssText insertRule setStringValue setProperty
    #    backgroundImage content cursor listStyleImage
    #    host hostname pathname port protocol search
    #    setNamedItem
    #    innerHTML outerHTML outerText body
    #    getElementById getElementsByTagName
    #    insertAdjacentHTML setAttribute setAttributeNode
    #    nodeValue
    #    value cookie domain frames parent top opener
    #    execScript execCommand navigate
    #    showModalDialog showModelessDialog
    #    LoadMovie
    #    ) ;
    #@RE_JS_SET_TRAPPED_PROPERTIES{@w}= (1) x @w ;

    #@w= qw(
    #    abstract boolean break byte case char class const continue debugger
    #    default delete do else enum export extends final finally float goto
    #    implements in instanceof int interface long native package private
    #    protected return short static synchronized throw throws transient
    #    try typeof void volatile
    #    ) ;
    #@RE_JS_SET_RESERVED_WORDS_NON_EXPRESSION{@w}= (1) x @w ;

    #@w= qw#
    #    { } ( ) [ ] . ; , < > <= >= == != === !== + - * % ++ -- << >> >>>
    #    & | ^ ! ~ && || ? : = += -= *= %= <<= >>= >>>= &= |= ^= / /=
    #    # ;
    #@RE_JS_SET_ALL_PUNCTUATORS{@w}= (1) x @w ;


    #-------------------------------------------------------------------------
    #  expressions
    #-------------------------------------------------------------------------

    # This section is not actually used in the program.  The "patterns" here
    #   won't quite work; they're only for studying, to work out how expressions
    #   are parsed in JavaScript.  The whole grammar of expressions is a kind of
    #   recursive network of many different productions (rules).  The set of
    #   patterns here is greatly condensed from the grammar productions in the
    #   ECMAScript spec, but is still accurate and expresses the basic
    #   framework.  One basic recursion loop is that:  Expression contains
    #   LeftHandSideExpression, which contains PrimaryExpression and Arguments,
    #   both of which may contain Expression.  If you think of Expression as
    #   being like a polynomial, then LeftHandSideExpression is similar to one
    #   term in it, and PrimaryExpression is similar to the central piece of
    #   that (e.g. a variable name, a number, or a parenthesized subexpression);
    #   Arguments is a standard comma-separated list of arguments.  This
    #   recursion loop has many more intermediate steps in the actual spec; a
    #   few that simplify the other patterns, or are referred to in their own
    #   right, are articulated below.
    # A few extra pseudo-productions are created here to simplify the rest of
    #   the grammar.  For example, the list of binary operators lets us
    #   summarize two full pages of productions into a one-line pattern.
    # Again, these are NOT actual working patterns!  So don't use them in their
    #   current state.  To make them work, the subexpressions in them that match
    #   tokens would have to be interspersed with allowed whitespace, e.g. by
    #   using $RE_JS_SKIP.  Also, regular expression literals would have to be
    #   fit in appropriately.  They're a quirk in the language definition, not
    #   used in the syntax productions-- during *parsing*, they're replaced by
    #   RegExp objects.  See the spec, section 7.8.5, for details.  Finally, any
    #   patterns that contain variables set after them must use "postponed
    #   subexpressions", i.e. the "(??{ $PATTERN })" construct.  This is how
    #   recursive (and mutually-referencing) patterns are expressed in Perl.  A
    #   pretty neat feature, actually, if you don't know about it yet.
    # If used for real, some of these patterns might benefit from being
    #   non-backtracking.  In some cases, they might even require that to parse
    #   correctly.  See notes about backtracking at the start of this routine.
    # For LeftHandSideExpression, we use a pattern that is simpler to work with
    #   than the pattern in the spec, but is not strictly accurate.  It's a
    #   superset of the real LeftHandSideExpression, so it should cover all
    #   valid JavaScript expressions.  An example of an expression that is not
    #   strictly allowed but would match our pattern is "new new foo(a).b(c)".

    # The next two aren't in the spec, but are useful to us below.
    # $RE_JS_BINARY_OPERATOR=  qr/instanceof|in|>>>=?|===|!==|<<=|>>=|[<>=!+*%&|^\/-]=|<<|>>|&&|\|\||[*\/%+<>&^|?:=-]/ ;
    # $RE_JS_UNARY_OPERATOR=   qr/delete|void|typeof|\+\+|--|[+~!-]/ ;

    # $RE_JS_ARRAY_LITERAL= qr/\[,*(?:$RE_JS_ASSIGNMENT_EXPRESSION(?:,+$RE_JS_ASSIGNMENT_EXPRESSION)*)?,*\]/ ;
    # $RE_JS_PROPERTY_NAME= qr/$RE_JS_IDENTIFIER_NAME|$RE_JS_STRING_LITERAL|$RE_JS_NUMERIC_LITERAL/ ;
    # $RE_JS_OBJECT_LITERAL= qr/{(?:$RE_JS_PROPERTY_NAME:$RE_JS_ASSIGNMENT_EXPRESSION
    #                               (?:,$RE_JS_PROPERTY_NAME:$RE_JS_ASSIGNMENT_EXPRESSION)*)?}/x ;

    # $RE_JS_ARGUMENTS= qr/\((?:$RE_JS_ASSIGNMENT_EXPRESSION(?:,$RE_JS_ASSIGNMENT_EXPRESSION)*)?\)/ ;

    # $RE_JS_FUNCTION_EXPRESSION= qr/function$RE_JS_IDENTIFIER_NAME?
    #                                \((?:$RE_JS_IDENTIFIER_NAME(?:,$RE_JS_IDENTIFIER_NAME)*)\)
    #                                {$RE_JS_PROGRAM}
    #                               /x ;


    # $RE_JS_PRIMARY_EXPRESSION= qr/$RE_JS_IDENTIFIER_NAME|$RE_JS_NUMERIC_LITERAL|$RE_JS_STRING_LITERAL|
    #                               $RE_JS_ARRAY_LITERAL|$RE_JS_OBJECT_LITERAL|\($RE_JS_EXPRESSION\)/ ;

    # Here's the approximate simplification.
    # $RE_JS_LEFT_HAND_SIDE_EXPRESSION= qr/(?:new)*
    #                                      (?:$RE_JS_PRIMARY_EXPRESSION|$RE_JS_FUNCTION_EXPRESSION)
    #                                      (?:$RE_JS_ARGUMENTS|\[$RE_JS_EXPRESSION\]|\.$RE_JS_IDENTIFIER_NAME)*
    #                                     /x ;


    # $RE_JS_UNARY_EXPRESSION= qr/$RE_JS_UNARY_OPERATOR*$RE_JS_LEFT_HAND_SIDE_EXPRESSION(?:\+\+|--)?/ ;

    # $RE_JS_ASSIGNMENT_EXPRESSION= qr/$RE_JS_UNARY_EXPRESSION(?:$RE_JS_BINARY_OPERATOR$RE_JS_UNARY_EXPRESSION)*/ ;

    # $RE_JS_EXPRESSION= qr/$RE_JS_ASSIGNMENT_EXPRESSION(?:,$RE_JS_ASSIGNMENT_EXPRESSION)*/ ;


    #-------------------------------------------------------------------------
    # Below are the various patterns that would strictly follow the spec,
    #   collected from above.
    #-------------------------------------------------------------------------

#   $RE_JS_LINE_TERMINATOR= qr/[\012\015]|\x{2028}|\x{2029}/ ;
#   $RE_JS_COMMENT= qr!(?>/\*.*?\*/|//[^\012\015\x{2028}\x{2029}]*)!s ;
#
#   $RE_JS_IDENTIFIER_START= qr/\p{Lu}|\p{Ll}|\p{Lt}|\p{Lm}|\p{Lo}|\p{Nl}|[\$_]|\\u[0-9a-fA-F]{4}/ ;
#   $RE_JS_IDENTIFIER_PART=  qr/$RE_JS_IDENTIFIER_START|\p{Mn}|\p{Mc}|\p{Nd}|\p{Pc}/ ;
#
#   $RE_JS_ESCAPE_SEQUENCE= qr/x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|0(?![0-9])|[^0-9xu\012\015\x{2028}\x{2029}]/ ;
#   $RE_JS_STRING_LITERAL= qr/"(?>(?:[^"\\\012\015\x{2028}\x{2029}]|\\$RE_JS_ESCAPE_SEQUENCE)*)"|
#			      '(?>(?:[^'\\\012\015\x{2028}\x{2029}]|\\$RE_JS_ESCAPE_SEQUENCE)*)'/x ;
#
#   $RE_JS_REGULAR_EXPRESSION_LITERAL= qr!/(?>(?:[^\012\015\x{2028}\x{2029}*\\/]|\\[^\012\015\x{2028}\x{2029}])
#					      (?:[^\012\015\x{2028}\x{2029}\\/]|\\[^\012\015\x{2028}\x{2029}])*)
#					  /(?>$RE_JS_IDENTIFIER_PART*)
#					 !x ;
#
#   $RE_JS_MEMBER_EXPRESSION= qr/(?:$RE_JS_PRIMARY_EXPRESSION|$RE_JS_FUNCTION_EXPRESSION)
#				   (?:\[$RE_JS_EXPRESSION\]|\.$RE_JS_IDENTIFIER_NAME)*
#				 |new$RE_JS_MEMBER_EXPRESSION$RE_JS_ARGUMENTS
#				/x ;
#   $RE_JS_LEFT_HAND_SIDE_EXPRESSION= qr/(?:new)*$RE_JS_MEMBER_EXPRESSION|
#					 $RE_JS_MEMBER_EXPRESSION$RE_JS_ARGUMENTS
#					 (?:$RE_JS_ARGUMENTS|\[$RE_JS_EXPRESSION\]|\.$RE_JS_IDENTIFIER_NAME)*
#					/x ;


}



#-----------------------------------------------------------------------
#  JavaScript library used when rewriting JavaScript
#-----------------------------------------------------------------------


# These are the functions included in the JavaScript library:
#   Initialization functions:
#     _proxy_jslib_init
#     _proxy_jslib_pass_vars (called from outside)
#   API functions:
#     _proxy_jslib_handle
#     _proxy_jslib_assign
#     _proxy_jslib_assign_rval
#   Secondary functions needed to support above functions:
#     _proxy_jslib_write_via_buffer
#     _proxy_jslib_flush_write_buffer
#     _proxy_jslib_new_function
#     _proxy_jslib_doc2win
#     _proxy_jslib_init_domain
#     _proxy_jslib_full_url
#     _proxy_jslib_full_url_by_frame
#     _proxy_jslib_cookie_to_client
#     _proxy_jslib_cookie_from_client
#     _proxy_jslib_proxify_html
#     _proxy_jslib_proxify_js
#     _proxy_jslib_proxify_comment
#     _proxy_jslib_proxify_script_block
#     _proxy_jslib_proxify_style_block
#     _proxy_jslib_proxify_decl_bang
#     _proxy_jslib_proxify_decl_question
#     _proxy_jslib_proxify_element
#     _proxy_jslib_proxify_attribute
#     _proxy_jslib_proxify_block
#     _proxy_jslib_proxify_css
#     _proxy_jslib_css_full_url
#     _proxy_jslib_return_frame_doc
#     _proxy_jslib_proxy_encode, _proxy_jslib_proxy_decode
#     _proxy_jslib_cookie_encode, _proxy_jslib_cookie_decode
#     _proxy_jslib_wrap_proxy_encode, _proxy_jslib_wrap_proxy_decode
#   Utilities:
#     _proxy_jslib_instanceof
#     _proxy_jslib_parse_url
#     _proxy_jslib_parse_full_url
#     _proxy_jslib_pack_flags
#     _proxy_jslib_unpack_flags
#     _proxy_jslib_html_escape
#     _proxy_jslib_html_unescape
#     _proxy_jslib_global_replace


# Returns the JavaScript library used to proxify JavaScript.  Normally, it
#   should be cachable.
# Some of these routines (the "API") are referenced from this Perl script.
#   Other routines are added to support the API functions.
# One important routine here is _proxy_jslib_pass_vars().  It's a general
#   mechanism used to pass any needed values from the Perl script into this
#   library.  One call to it is inserted in the HTML, right after this JS
#   library is loaded.  To pass more values into this library, add arguments
#   where it is called (two places), and modify the routine itself below.
# Many routines here are analogous to Perl routines in this script.  Some are
#   almost exact translations of the Perl routines into JavaScript (thus
#   implying that whenever those Perl routines are changed, these JS routines
#   must be changed too).
# To make this code run in MSIE 5.0, we must avoid a few JavaScript features
#   that are not supported in it.  :P  These include the boolean "in" operator,
#   Array.{pop,push,shift,unshift,splice}, Function.{apply,call},
#   String.replace() with a replacement function, certain regular expression
#   constructs, and (yes) the keyword-like global property "undefined" (though
#   the value exists and can be created with "void 0").  Also, instanceof
#   doesn't always work right in MSIE so avoid that too.
# Update:  It's been a few years now that everyone has supported JS 1.5, so
#   as of 9-07 it's allowed to use some of those features above.
# Note that MSIE's Array.splice() doesn't work with one parameter, so always
#   include the second parameter when calling it.
# This library contains very little commenting, to save bandwidth.  For those
#   routines with Perl analogs, see the comments accompanying the Perl routines.
sub return_jslib {
    my($date_header)=    &rfc1123_date($now, 0) ;
    my($expires_header)= &rfc1123_date($now+86400*7, 0) ;  # expires after a week

    # To save time, only set $JSLIB_BODY if it hasn't been set already.
    unless ($JSLIB_BODY) {

	# We must use single-quoted line delimiter ('EOF') to prevent variable
	#   interpolation, etc.  But we also have to pass some constants to it,
	#   so we concatenate a "variable" block and a "fixed" block.  The
	#   "variable" block is constant for each installation, so the library
	#   can still be cached.
	# Note that $ENCODE_DECODE_BLOCK_IN_JS is a user config setting, at top.
	my($script_name_jsq)= $ENV_SCRIPT_NAME ;
	$script_name_jsq=~ s/(["\\])/\\$1/g ;   # make safe for JS quoted string
	my($script_url_jsq)= $script_url ;
	$script_url_jsq=~ s/(["\\])/\\$1/g ;   # make safe for JS quoted string
	my($THIS_HOST_jsq)= $THIS_HOST ;
	$THIS_HOST_jsq=~ s/(["\\])/\\$1/g ;   # make safe for JS quoted string
	my($proxy_group_jsq, @pg, $all_types_js, $mime_type_id_js) ;
	@pg= @PROXY_GROUP ;
	foreach (@pg) { s/(["\\])/\\$1/g }
	$proxy_group_jsq= join(', ', map { "'$_'" } @pg) ;
	$all_types_js=    join(', ', map { "'$_'" } @ALL_TYPES) ;
	$mime_type_id_js= join(', ', map { "'$_':$MIME_TYPE_ID{$_}" } keys %MIME_TYPE_ID) ;

	$JSLIB_BODY= <<EOV . <<'EOF' ;

var _proxy_jslib_SCRIPT_NAME= "$script_name_jsq" ;
var _proxy_jslib_SCRIPT_URL= "$script_url_jsq" ;
var _proxy_jslib_THIS_HOST= "$THIS_HOST_jsq" ;
var _proxy_jslib_PROXY_GROUP= [$proxy_group_jsq] ;
var _proxy_jslib_ALL_TYPES= [$all_types_js] ;
var _proxy_jslib_MIME_TYPE_ID= {$mime_type_id_js} ;

$ENCODE_DECODE_BLOCK_IN_JS

EOV

var _proxy_jslib_browser_family ;
var _proxy_jslib_RE_FULL_PATH ;
var _proxy_jslib_url_start, _proxy_jslib_url_start_inframe, _proxy_jslib_url_start_noframe,
    _proxy_jslib_is_in_frame, _proxy_jslib_packed_flags, _proxy_jslib_URL ;
var _proxy_jslib_cookies_are_banned_here, _proxy_jslib_doing_insert_here, _proxy_jslib_SESSION_COOKIES_ONLY,
    _proxy_jslib_COOKIE_PATH_FOLLOWS_SPEC, _proxy_jslib_RESPECT_THREE_DOT_RULE,
    _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, _proxy_jslib_RTMP_SERVER_PORT,
    _proxy_jslib_default_script_type, _proxy_jslib_default_style_type,
    _proxy_jslib_USE_DB_FOR_COOKIES, _proxy_jslib_COOKIES_FROM_DB ;
var _proxy_jslib_RE, _proxy_jslib_ARRAY64, _proxy_jslib_UNARRAY64 ;
var _proxy_jslib_needs_jslib, _proxy_jslib_does_write ;
var _proxy_jslib_write_buffers= [ {doc:document, has_js:true} ] ;
var _proxy_jslib_ret ;
var _proxy_jslib_current_object_classid ;
var _proxy_jslib_increments= {applets: 0, embeds: 0, forms: 0, ids: 0, layers: 0, anchors: 0, images: 0, links: 0} ;

// these must be updated when adding handled properties to _handle() or _assign()!
var _proxy_jslib_handle_properties= 'eval insertAdjacentHTML setAttribute setAttributeNode getAttribute insertRule innerHTML outerHTML outerText src currentSrc href background lowsrc action formAction useMap longDesc cite codeBase location poster open assign write writeln URL url newURL oldURL referrer baseURI body replace toString String setInterval setTimeout cookie domain frames parent top opener protocol host hostname port pathname search setStringValue setProperty setNamedItem load execScript navigate showModalDialog showModelessDialog execCommand LoadMovie getElementById getElementsByTagName appendChild replaceChild insertBefore close origin postMessage pushState replaceState'.split(/\s+/) ;

var _proxy_jslib_assign_properties= 'background src href lowsrc action useMap longDesc cite codeBase location poster profile cssText innerHTML outerHTML outerText nodeValue protocol host hostname port pathname search cookie domain value backgroundImage content cursor listStyle listStyleImage text textContent'.split(/\s+/) ;

var _proxy_jslib_handle_props_hash, _proxy_jslib_assign_props_hash ;


// Hack for sites that redefine core JavaScript objects.  :P
// Add more properties as needed.
//var _proxy_jslib_ORIGINAL_ARRAY= {push: Array.prototype.push} ; // for some reason this doesn't work
// This fails in MSIE, so put them in try/catch.
try { var _proxy_jslib_ORIGINAL_ARRAY_push= Array.prototype.push } catch(e) {}
try { var _proxy_jslib_ORIGINAL_WINDOW_alert= Window.prototype.alert } catch(e) {}



_proxy_jslib_init() ;


//---- first, the initialization functions -----------------------------

// set _proxy_jslib_URL, _proxy_jslib_url_start, _proxy_jslib_packed_flags,
//   _proxy_jslib_is_in_frame, _proxy_jslib_url_start_inframe, _proxy_jslib_url_start_noframe
function _proxy_jslib_init() {
    _proxy_jslib_browser_family=
	    navigator.appName.match(/Netscape/i)   ? 'netscape'
	  : navigator.appName.match(/Microsoft/i)  ? 'msie'
	  : '' ;

    _proxy_jslib_set_RE() ;

    _proxy_jslib_ARRAY64=
	'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'.split('') ;
    _proxy_jslib_UNARRAY64= {} ;
    for (var i= 0 ; i<64 ; i++) { _proxy_jslib_UNARRAY64[_proxy_jslib_ARRAY64[i]]= i }


    // initialize property-list hashes for _proxy_jslib_handle() and
    //   _proxy_jslib_assign()
    _proxy_jslib_handle_props_hash= {} ;
    for (var i= 0 ; i<_proxy_jslib_handle_properties.length ; i++)
	_proxy_jslib_handle_props_hash['p_'+_proxy_jslib_handle_properties[i]]= true ;
    _proxy_jslib_assign_props_hash= {} ;
    for (var i= 0 ; i<_proxy_jslib_assign_properties.length ; i++)
	_proxy_jslib_assign_props_hash['p_'+_proxy_jslib_assign_properties[i]]= true ;


    // create global regex that matches a full URL, needed for _proxy_jslib_parse_full_url()
    // if being run from a daemon, make this something that won't choke inside parens
    var RE_SCRIPT_NAME= (_proxy_jslib_SCRIPT_NAME!='')
		? _proxy_jslib_SCRIPT_NAME.replace(/(\W)/g, function (p) { return '\\'+p } )
		: '.{0}' ;   // because "()" in a regex may throw an error
    _proxy_jslib_RE_FULL_PATH= new RegExp('^('+RE_SCRIPT_NAME+')\\/?([^\\/]*)\\/?(.*)') ;

    // Mozilla sometimes adds 'wyciwyg://' to the URL
    var URL= document.URL.replace(/^wyciwyg:\/\/\d+\//i, '') ;

    var u= _proxy_jslib_parse_full_url(URL) ;
    if (_proxy_jslib_PROXY_GROUP.length) {
	_proxy_jslib_url_start= _proxy_jslib_PROXY_GROUP[Math.floor(Math.random()*_proxy_jslib_PROXY_GROUP.length)]
				+'/'+u[1]+'/' ;
    } else {
	_proxy_jslib_url_start= u[0]+'/'+u[1]+'/' ;
    }
    var flags= _proxy_jslib_unpack_flags(u[1]) ;
    _proxy_jslib_is_in_frame= flags[5] ;
    flags[5]= 1 ;    // that's the frame flag
    _proxy_jslib_url_start_inframe= u[0]+'/'+_proxy_jslib_pack_flags(flags)+'/' ;
    flags[5]= 0 ;
    _proxy_jslib_url_start_noframe= u[0]+'/'+_proxy_jslib_pack_flags(flags)+'/' ;

    _proxy_jslib_packed_flags= u[1] ;
    _proxy_jslib_URL=          u[2] ;

    // this begins life as the hostname.  document.URL may not be set yet, so send URL.
    _proxy_jslib_init_domain(window, _proxy_jslib_URL) ;

    // call _proxy_jslib_onload() and possibly an existing window.onload()
    // make sure _proxy_jslib_onload() is called even if window.onload() fails.
    var old_onload= window.onload ;
    window.onload= function() {
		       try { if (old_onload) old_onload() } catch(e) {} ;
		       _proxy_jslib_onload() ;
		   }

//alert('end of init; _p_j_URL=\n['+_proxy_jslib_URL+']') ;
}


// set variables passed in from Perl program.
function _proxy_jslib_pass_vars(base_url, cookies_are_banned_here, doing_insert_here, SESSION_COOKIES_ONLY, COOKIE_PATH_FOLLOWS_SPEC, RESPECT_THREE_DOT_RULE, ALLOW_UNPROXIFIED_SCRIPTS, RTMP_SERVER_PORT, default_script_type, default_style_type, USE_DB_FOR_COOKIES, COOKIES_FROM_DB) {
    // set base_ vars from base_url
    _proxy_jslib_set_base_vars(window.document, base_url) ;

    // other settings
    _proxy_jslib_cookies_are_banned_here=   cookies_are_banned_here ;
    _proxy_jslib_doing_insert_here=         doing_insert_here ;
    _proxy_jslib_SESSION_COOKIES_ONLY=      SESSION_COOKIES_ONLY ;
    _proxy_jslib_COOKIE_PATH_FOLLOWS_SPEC=  COOKIE_PATH_FOLLOWS_SPEC ;
    _proxy_jslib_RESPECT_THREE_DOT_RULE=    RESPECT_THREE_DOT_RULE ;
    _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS= ALLOW_UNPROXIFIED_SCRIPTS ;
    _proxy_jslib_USE_DB_FOR_COOKIES=        USE_DB_FOR_COOKIES ;
    _proxy_jslib_COOKIES_FROM_DB=           COOKIES_FROM_DB ;
    _proxy_jslib_RTMP_SERVER_PORT=          RTMP_SERVER_PORT || 1935 ;   // jsm-- get a better solution...

    _proxy_jslib_default_script_type=      default_script_type.toLowerCase() ;
    _proxy_jslib_default_style_type=       default_style_type.toLowerCase() ;
}


// lastly, do what's needed after the document fully loads
function _proxy_jslib_onload() {

    // if we're in frames, then try to update the URL in the top form
    if (_proxy_jslib_is_in_frame && (window.parent===window.top) && top._proxy_jslib_insertion_frame)
	top._proxy_jslib_insertion_frame.document.URLform.URL.value= _proxy_jslib_URL ;

}


//---- the general handler routines _proxy_jslib_handle() and _proxy_jslib_assign() ----

// This is used when the property in question IS NOT being assigned to.
function _proxy_jslib_handle (o, property, cur_val, calls_now, in_new_statement) {
    //  performance tweak
    if (typeof(property)=='number') return _handle_default() ;

    // guess when the window object is implied; this only matters with Window's
    //   properties that we handle below
    if ((o===null)  && (typeof(property)=='string') && property.match(/^(location|open|setInterval|setTimeout|frames|parent|top|opener|execScript|navigate|showModalDialog|showModelessDialog|parentWindow|String)$/) && (window[property]===cur_val)) o= window ;

    // handle eval() specially-- it (oddly) can be a property of any object
    if (property=='eval') {
	if ((o!=null) && (o.eval)) {
	    var oldeval= o.eval ;
	    return function (code) {
		       // return o.eval(_proxy_jslib_proxify_js(code, 0)) ;
		       var ret ;
		       o._proxy_jslib_oldeval= oldeval ;
		       ret= o._proxy_jslib_oldeval(_proxy_jslib_proxify_js(code, 0)) ;
		       delete o._proxy_jslib_oldeval ;
		       return ret ;
		   } ;
	} else {
	    if (o!=null) return undefined ;
	    var oldeval= eval ;
	    return function (code) {
		       return oldeval(_proxy_jslib_proxify_js(code, 0)) ;
		   } ;
	}
    }

    // if object is still null, merely return property value
    if (o==null) return cur_val ;


    // allow things like "if (element.insertAdjacentHTML)" to work as expected
    if (typeof(o)=='object' && !(property in o)) return void 0 ;


    // StorageList needs unique handling
    // Safari chokes here, so wrap in try/catch
    try {
	if ((_proxy_jslib_browser_family!='msie') && (o instanceof StorageList)) {
	    return o[property+'.cgiproxy.'+_proxy_jslib_THIS_HOST] ;
	}
    } catch(e) {} ;


    // performance tweak
    if (!_proxy_jslib_handle_props_hash['p_'+property]) return _handle_default() ;


    // If object is an XML Element, don't proxify anything.  There is no
    //   explicit XMLElement type, but any Element that's not HTMLElement is
    //   an XML Element.
    // This should be cleaned up and possibly merged with _p_j_instanceof().
    if (_proxy_jslib_instanceof(o, 'Element') && !_proxy_jslib_instanceof(o, 'HTMLElement')) {
	return _handle_default() ;
    }


    // Main switch

    // note use of closures to remember the object o
    // note also that in returned functions, we use "this" if it is available;
    //   see comments above proxify_js() (Perl routine)
    // Store new windows in a list so we can insert JS later if needed.
    // Store windows instead of documents, because docs may not be created yet.

    switch (property) {

	// because some sites modify these in place, we must un-proxify these
	//   when retrieving the value.
	// for Location and Link objects, return the object, but handle
	//   toString() below to unproxify it when needed.
	// jsm-- this will still leave Location or Link proxified when
	//   toString() is called implicitly.
	case 'src':
	case 'href':
	case 'background':
	case 'lowsrc':
	case 'action':
	case 'formAction':
	case 'useMap':
	case 'longDesc':
	case 'cite':
	case 'codeBase':
	case 'location':
	case 'baseURI':
	case 'poster':
	    var u= (o!=void 0) ? o[property] : cur_val ;
	    if (u==void 0) return void 0 ;
	    if (typeof u=='number') return u ;
	    // return unchanged if u is a non-String object
	    if (u && (typeof u=='object') && !('toLowerCase' in u))
		return u ;
	    // return unchanged if o is not a Node or a Location
	    if (!_proxy_jslib_instanceof(o, 'Node') && !_proxy_jslib_instanceof(o, 'Location')) return u ;
	    var pu= _proxy_jslib_parse_full_url(u) ;
	    if (pu==void 0) return u ;   // if it's not a URL
//if (u=='') alert('in handle, first switch; typeof, o, property, u, caller=['+typeof(o)+']['+o+']['+property+']['+u+']\n['+arguments.callee.caller.caller+']') ;
	    return pu[2] ;


	case 'open':
	    if (_proxy_jslib_instanceof(o, 'XMLHttpRequest')) {
		return function(method, url, asyncflag, username, password) {
			   if (this!==window) o= this ;
			   // if absolute URL, verify domain is same as current page
			   if (url.toString().match(/^[\w\+\.\-]*\:/)) {
			       var h1= (_proxy_jslib_parse_url(_proxy_jslib_URL))[4] ;
			       var h2= (_proxy_jslib_parse_url(url))[4] ;
			       var d1, d2, m ;
//alert('h1,h2,url=['+h1+']['+h2+']\n['+url+']') ;
			       // for 2-char TLDs, require an extra domain segment
			       m= h1.match(/(^|\.)([\w-]+\.[\w-]+(\.\w\w)?)$/) ;
			       var d1= m  ? m[2].toLowerCase()  : void 0 ;
			       m= h2.match(/(^|\.)([\w-]+\.[\w-]+(\.\w\w)?)$/) ;
			       var d2= m  ? m[2].toLowerCase()  : void 0 ;
			       if (d1==void 0 || d2==void 0 || d1!=d2) {   // unallowed domain
				   alert('disallowed domain on XMLHttpRequest: ['+d2+'], should be ['+d1+']') ;
				   return ;
			       }
			   }

			   // proxify the URL using 'x-proxy/xhr' as the expected type
			   var flags= _proxy_jslib_unpack_flags(_proxy_jslib_packed_flags) ;
			   flags[5]= 1 ;  // because of how this is used, don't insert the top form
			   flags[6]= 'x-proxy/xhr' ;

			   var old_url_start= _proxy_jslib_url_start ;
			   _proxy_jslib_url_start= _proxy_jslib_SCRIPT_URL + '/' + _proxy_jslib_pack_flags(flags) + '/' ;
			   url= _proxy_jslib_full_url(url) ;
			   _proxy_jslib_url_start= old_url_start ;

			   return o.open(method, url, asyncflag, username, password) ;
		       } ;

	    } else if (_proxy_jslib_instanceof(o, 'Window')) {
		return function (url, name, features, replace) {
			   if (this!==window) o= this ;
			   var full_url= _proxy_jslib_full_url(url) ;
			   var win= o.open(full_url, name, features, replace) ;
			   if (url) _proxy_jslib_init_domain(win) ;
			   // in the absence of spec, "about:blank" domain is that of parent window
			   else win._proxy_jslib_document_domain= o._proxy_jslib_document_domain ;
			   return win ;
		       } ;

	    } else if (_proxy_jslib_instanceof(o, 'Document')) {
		return function(arg1, name, features, replace) {
			   // arg1 should default to "text/html", but it doesn't
			   //   always in Firefox, so we force it
			   if (arg1==void 0) arg1= 'text/html' ;
			   if (this!==window) o= this ;
			   if (arguments.length<=2) {
//alert('about to Document.open; win=['+_proxy_jslib_doc2win(o)+']') ;
			       return o.open(arg1, name) ;
			   } else {
			       // MSIE-specific
			       return o.open(_proxy_jslib_full_url(arg1, o), name, features, replace) ;
			   }
		       } ;
	    } else {
		return _handle_default() ;
	    }


	case 'write':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		// buffer the output by document
		// no return value
		return function () {
			   if (this!==window) o= this ;
			   for (var i= 0 ; i<arguments.length ; i++)
			       _proxy_jslib_write_via_buffer(o, arguments[i]) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }
	case 'writeln':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		// buffer the output by document
		// no return value
		return function () {
			   if (this!==window) o= this ;
			   for (var i= 0 ; i<arguments.length ; i++)
			       _proxy_jslib_write_via_buffer(o, arguments[i]) ;
			   _proxy_jslib_write_via_buffer(o, '\n') ;
		       } ;
	    } else {
		return _handle_default() ;
	    }


	case 'close':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		return function() {
			   if (this!==window) o= this ;
//alert('starting Document.close(); # buffers='+_proxy_jslib_write_buffers.length) ;  //  jsm-- all alerts and confirms
			   var buf, i, p ;
			   for (i in _proxy_jslib_write_buffers) {
			       if (_proxy_jslib_write_buffers[i].doc===o) {
				   buf= _proxy_jslib_write_buffers[i] ;
				   if (buf.buf==void 0) break ;
				   p= _proxy_jslib_proxify_html(buf.buf, o, !buf.has_js) ;
				   if (p[3]) return ;   // found frame document
//if (confirm('flushing one buffer;\nhas_js=['+p[2]+']\nout=['+p[0]+']'))
				   buf.has_js= false ;
				   buf.buf= void 0 ;
				   o.write(p[0]) ;
				   break ;
			       }
			   }
//alert('about to o.close()') ;
			   o.close() ;
//alert('ending Document.close()') ;
		       } ;
	    } else {
		return _handle_default() ;
	    }


	case 'innerHTML':
	case 'outerHTML':
	case 'outerText':
	    // only unproxify it if the object is an HTMLElement or HTMLDocument
	    if ((_proxy_jslib_instanceof(o, 'HTMLElement') || _proxy_jslib_instanceof(o, 'HTMLDocument'))
		&& !is_in_script(o, property))
	    {
		return _proxy_jslib_proxify_html(o[property], (o.ownerDocument || o), false, true)[0] ;  // unproxifies
	    } else {
		return _handle_default() ;
	    }


	case 'url':
	    if (_proxy_jslib_instanceof(o, 'EventSource')) {
		var pu= _proxy_jslib_parse_full_url(o[property]) ;
		if (pu==void 0) return void 0 ;
		return pu[2] ;
	    } else {
		return _handle_default() ;
	    }

	case 'newURL':
	case 'oldURL':
	    if (_proxy_jslib_instanceof(o, 'HashChangeEvent')) {
		var pu= _proxy_jslib_parse_full_url(o[property]) ;
		if (pu==void 0) return void 0 ;
		return pu[2] ;
	    } else {
		return _handle_default() ;
	    }



	case 'getElementById':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		// Hack-- if element isn't in doc yet but is in output buffer, flush
		//   buffer and try again.
		return function (elementId) {
			   if (this!==window) o= this ;
			   var e, i, buf, p ;
			   e= o.getElementById(elementId) ;
			   if (e!=null) return e ;
			   for (i= 0 ; i<_proxy_jslib_write_buffers.length ; i++)
			       if (_proxy_jslib_write_buffers[i]  &&
				   _proxy_jslib_write_buffers[i].doc===o) break ;
			   if (i>=_proxy_jslib_write_buffers.length) return null ;
			   buf= _proxy_jslib_write_buffers[i] ;
			   if (buf.buf==void 0) return null ;
			   if (buf.buf.match(new RegExp('id\\s*=\\s*[\'"]?\\s*'+elementId+'\\s*[\'"]?', 'i'))) {
			       p= _proxy_jslib_proxify_html(buf.buf, o, false) ;
			       if (p[3]) return ;   // found frame document
			       buf.has_js= buf.has_js || p[2] ;
			       buf.buf= p[1] ;
			       o.write(p[0]) ;
			   }
			   return o.getElementById(elementId) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'getElementsByTagName':
	    if (_proxy_jslib_instanceof(o, 'Document') || _proxy_jslib_instanceof(o, 'Element')) {
		return function (tagname) {
			   if (this!==window) o= this ;
			   var i, buf, pi, doc ;
			   doc= (o.ownerDocument || o) ;
			   for (i= 0 ; i<_proxy_jslib_write_buffers.length ; i++)
			       if (_proxy_jslib_write_buffers[i]  &&
				   _proxy_jslib_write_buffers[i].doc===doc) break ;
			   if (i>=_proxy_jslib_write_buffers.length) return o.getElementsByTagName(tagname) ;
			   buf= _proxy_jslib_write_buffers[i] ;
			   if (buf.buf==void 0) return o.getElementsByTagName(tagname) ;
			   if (tagname=='*' || buf.buf.match(new RegExp('<'+tagname+'\\b', 'i'))) {
			       p= _proxy_jslib_proxify_html(buf.buf, doc, false) ;
			       if (p[3]) return ;   // found frame document
			       buf.has_js= buf.has_js || p[2] ;
			       buf.buf= p[1] ;
			       doc.write(p[0]) ;
			   }
			   return o.getElementsByTagName(tagname) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'appendChild':
	    if (_proxy_jslib_instanceof(o, 'Node')) {
		return function (child) {
			   if ((o.nodeName.toLowerCase()=='script') && (child.nodeType==3)) { // TEXT_NODE=3
			       var type= o.type || _proxy_jslib_default_script_type ;
			       var new_text= _proxy_jslib_proxify_block(child.data, type,
				   _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, false) ;
			       return o.appendChild(document.createTextNode(new_text)) ;
			   } else if ((o.nodeName.toLowerCase()=='style') && child.nodeType==3) {
			       var type= o.type || _proxy_jslib_default_style_type ;
			       var new_text= _proxy_jslib_proxify_block(child.data, type,
				   _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, false) ;
			       return o.appendChild(document.createTextNode(new_text)) ;
			   } else {
			       return o.appendChild(child);
			   }
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'replaceChild':
	case 'insertBefore':
	    if (_proxy_jslib_instanceof(o, 'Node')) {
		return function (child, old_child) {
			   if ((o.nodeName.toLowerCase()=='script') && (child.nodeType==3)) { // TEXT_NODE=3
			       var type= o.type || _proxy_jslib_default_script_type ;
			       var new_text= _proxy_jslib_proxify_block(child.data, type,
				   _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, false) ;
			       return o[property](document.createTextNode(new_text), old_child) ;
			   } else if ((o.nodeName.toLowerCase()=='style') && child.nodeType==3) {
			       var type= o.type || _proxy_jslib_default_style_type ;
			       var new_text= _proxy_jslib_proxify_block(child.data, type,
				   _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, false) ;
			       return o[property](document.createTextNode(new_text), old_child) ;
			   } else {
			       return o[property](child, old_child);
			   }
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'createElement':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		return function (localName) {
			   var ret= o.createElement(localName) ;
			   if (localName.toLowerCase()=='iframe') _proxy_jslib_init_iframe(ret) ;
			   return ret ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'insertAdjacentHTML':
	    if (_proxy_jslib_instanceof(o, 'HTMLElement')) {
		return function (where, text) {
			   if (this!==window) o= this ;
			   return o.insertAdjacentHTML(where, _proxy_jslib_proxify_html(text, o.ownerDocument, false)[0]) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'setAttribute':
	    // MSIE can't do instanceof Element  :P
	    // if (!(o instanceof Element)) break ;   // go to default action
	    if (_proxy_jslib_instanceof(o, 'Element')) {
		return function (name, value) {
			   if (this!==window) o= this ;
			   return o.setAttribute(name.toLowerCase(), _proxy_jslib_proxify_attribute(o, name, value)) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'setAttributeNode':
	    if (_proxy_jslib_instanceof(o, 'Element')) {
		return function (newAttr) {
			   if (this!==window) o= this ;
			   newAttr.nodeValue= _proxy_jslib_proxify_attribute(o, newAttr.nodeName, newAttr.nodeValue) ;
			   return o.setAttributeNode(newAttr) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }
	case 'getAttribute':
	    if (_proxy_jslib_instanceof(o, 'Element')) {
		return function (name, flag) {
			   var attr_val= o.getAttribute(name, flag) ;
			   return _proxy_jslib_proxify_attribute(o, name, attr_val, 1) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'insertRule':
	    if (_proxy_jslib_instanceof(o, 'CSSStyleSheet')) {
		return function (rule, index) {
			   if (this!==window) o= this ;
			   return o.insertRule(_proxy_jslib_proxify_css(rule), index) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'URL':
	case 'referrer':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		var pu= _proxy_jslib_parse_full_url(o[property]) ;
		return (pu==void 0)  ? void 0  : pu[2] ;
	    } else {
		return _handle_default() ;
	    }

	case 'body':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		var ret= o.getElementById('_proxy_css_main_div') ;
		return ret  ? ret  : o.body ;
	    } else {
		return _handle_default() ;
	    }

	case 'assign':
	    if (_proxy_jslib_instanceof(o, 'Location')) {
		return function(url) {
			   o.assign(_proxy_jslib_full_url(url)) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'replace':
	    if (_proxy_jslib_instanceof(o, 'Location')) {
		return function (url) {
			   if (this!==window) o= this ;
			   var u= _proxy_jslib_parse_full_url(o.toString()) ;
			   if (u!=void 0 && u[1]!='') {
			       return o.replace(_proxy_jslib_full_url_by_frame(url, null, _proxy_jslib_unpack_flags(u[1])[5])) ;
			   } else {
			       return o.replace(_proxy_jslib_full_url(url)) ;
			   }
		       } ;
	    } else {
		return _handle_default() ;
	    }
	    
	case 'toString':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		return function () {
			   if (this!==window) o= this ;
			   return _proxy_jslib_parse_full_url(o.toString())[2] ;
		       }
	    } else {
		return _handle_default() ;
	    }


	case 'setInterval':
	case 'setTimeout':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		var oldmethod= o[property] ;

		// Function.apply() not available in MSIE, yet "Function.apply"
		//   returns true, so just trap all errors.
		// jsm-- this will also trap any errors in called routines....
		return function (codefunc, time) {
			   if (this!==window) o= this ;
			   try {
			       if (typeof(codefunc)=='function') {
				   return oldmethod.apply(o, arguments) ;
			       } else {
				   return oldmethod.call(o, _proxy_jslib_proxify_js(codefunc), time) ;
			       }
			   } catch (e) {
			       var ret ;
			       o._proxy_jslib_oldmethod= oldmethod ;
			       if (typeof(codefunc)=='function') {
				   ret= o._proxy_jslib_oldmethod(codefunc, time) ;
			       } else {
				   ret= o._proxy_jslib_oldmethod(_proxy_jslib_proxify_js(codefunc), time) ;
			       }
			       try {
				   delete o._proxy_jslib_oldmethod ;
			       } catch(e) {
			       }
			       return ret ;
			   }
		} ;

	    } else {
		return _handle_default() ;
	    }


	case 'cookie':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		return _proxy_jslib_cookie_from_client(o) ;
	    } else {
		return _handle_default() ;
	    }


	case 'domain':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		// technically, Document.domain is just the hostname, though
		//   the same-origin policy uses scheme, hostname, and port
		var w= _proxy_jslib_doc2win(o) ;
		if (!w._proxy_jslib_document_domain) _proxy_jslib_init_domain(w) ;
		if (w._proxy_jslib_document_domain.match(/^https?\:\/\//))
		    return _proxy_jslib_parse_url(w._proxy_jslib_document_domain)[4] ;
//else alert("bad w._proxy_jslib_document_domain: " + w._proxy_jslib_document_domain) ;   // jsm-- remove
	    } else {
		return _handle_default() ;
	    }



	case 'frames':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		var f, ret= [], useret ;
		if (!_proxy_jslib_document_domain) _proxy_jslib_init_domain(window) ;
		for (f=0 ; f<o.frames.length ; f++) {
		    try {
			if (!o.frames[f]._proxy_jslib_document_domain) _proxy_jslib_init_domain(o.frames[f]) ;
			if ((o.frames[f]._proxy_jslib_document_domain!=_proxy_jslib_document_domain)
			    && (o.frames[f]._proxy_jslib_document_domain))
			{
//alert('frame differs in domain; f, domains of window, o.frames[f]=['+f+']['+_proxy_jslib_document_domain+']['+o.frames[f]._proxy_jslib_document_domain+']') ;  // jsm-- test a bunch, then remove
			    // include both the numbered frame and the (non-standard) named frame
			    ret[f]= _proxy_jslib_dup_window_safe(o.frames[f]) ;
			    if (o.frames[f].name) ret[o.frames[f].name]= ret[f] ;
			    useret= true ;
			} else {
			    ret[f]= o.frames[f] ;
			    if (o.frames[f].name) ret[o.frames[f].name]= ret[f] ;
			}
		    } catch (e) {
alert('Window.frames error: '+e) ;
		    }
		}
		return useret  ? ret  : o.frames ;

	    } else {
		return _handle_default() ;
	    }


	case 'parent':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		// if we're in main frame, pretend it's its own "parent".
		var w= (o.top._proxy_jslib_main_frame===o)  ? o  : o.parent ;
		if (!_proxy_jslib_document_domain) _proxy_jslib_init_domain(window) ;
		if (!w._proxy_jslib_document_domain) _proxy_jslib_init_domain(w) ;
		if (w._proxy_jslib_document_domain && (w._proxy_jslib_document_domain!=_proxy_jslib_document_domain)) {
//		    alert('Tried to access parent window, but has different domain; domains are [' + _proxy_jslib_document_domain + '] and [' + w._proxy_jslib_document_domain + ']') ;
		    return void 0 ;
		}
		return w ;
	    } else {
		return _handle_default() ;
	    }

	case 'top':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		// if window uses frames, translate "top" to "top._proxy_jslib_main_frame".
		var w= (o.top._proxy_jslib_main_frame!==void 0)  ? o.top._proxy_jslib_main_frame  : o.top ;
		if (!_proxy_jslib_document_domain) _proxy_jslib_init_domain(window) ;
		if (!w._proxy_jslib_document_domain) _proxy_jslib_init_domain(w) ;
		if (w._proxy_jslib_document_domain && (w._proxy_jslib_document_domain!=_proxy_jslib_document_domain)) {
//		    alert('Tried to access top window, but has different domain; domains are [' + _proxy_jslib_document_domain + '] and [' + w._proxy_jslib_document_domain + ']') ;
		    return void 0 ;
		}
		return w ;
	    } else {
		return _handle_default() ;
	    }

	case 'opener':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		if (!o.opener) return null ;
		if (!_proxy_jslib_document_domain) _proxy_jslib_init_domain(window) ;
		if (!o.opener._proxy_jslib_document_domain) _proxy_jslib_init_domain(o.opener) ;
		if (o.opener._proxy_jslib_document_domain && (o.opener._proxy_jslib_document_domain!=_proxy_jslib_document_domain)) {
//		    alert('Tried to access opener window, but has different domain; domains are [' + _proxy_jslib_document_domain + '] and [' + w._proxy_jslib_document_domain + ']') ;
		    return void 0 ;
		}
		return o.opener ;
	    } else {
		return _handle_default() ;
	    }


	//  _proxy_jslib_parse_url() returns full_match, protocol, authentication, host, hostname, port, pathname, search, hash

	case 'protocol':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		return _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(o.href)[2])[1] ;
	    } else {
		return _handle_default() ;
	    }

	case 'host':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		return _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(o.href)[2])[3] ;
	    } else {
		return _handle_default() ;
	    }

	case 'hostname':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		return _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(o.href)[2])[4] ;
	    } else {
		return _handle_default() ;
	    }

	case 'port':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		return _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(o.href)[2])[5] ;
	    } else {
		return _handle_default() ;
	    }

	case 'pathname':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		return _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(o.href)[2])[6] ;
	    } else {
		return _handle_default() ;
	    }

	case 'search':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		return _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(o.href)[2])[7] ;
	    } else {
		return _handle_default() ;
	    }



	case 'LoadMovie':
	    if (_proxy_jslib_instanceof(o, 'FlashPlayer')) {
		return function (layer, url) {
			   if (this!==window) o= this ;
			   return o.LoadMovie(layer, _proxy_jslib_full_url(url)) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }


	case 'setStringValue':
	    if (_proxy_jslib_instanceof(o, 'CSSPrimitiveValue')) {
		return function (type, value) {
			   if (this!==window) o= this ;
			   if (type==CSSPrimitiveValue.CSS_URI)
			       return o.setStringValue(type, _proxy_jslib_full_url(value)) ;
			   return o.setStringValue(type, value) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'setProperty':
	    if (_proxy_jslib_instanceof(o, 'CSSStyleDeclaration')) {
		return function (name, value, priority) {
			   if (this!==window) o= this ;
			   return o.setProperty(name, _proxy_jslib_proxify_css(value), priority) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'setNamedItem':
	    if (_proxy_jslib_instanceof(o, 'NamedNodeMap')) {
		return function (node) {
			   if (this!==window) o= this ;
			   node.nodeValue= _proxy_jslib_proxify_attribute(o, node.nodeName, node.nodeValue) ;
			   return o.setNamedItem(node) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }


	// Deproxify String() parameter if it's a Link or Location
	case 'String':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		return function(s) {
			   if (_proxy_jslib_instanceof(s, 'Link') || _proxy_jslib_instanceof(s, 'Location'))
			       return _proxy_jslib_parse_full_url(s.href)[2];
			   return String(s);
		       } ;
	    } else {
		return _handle_default() ;
	    }


	// Next two go together
	// jsm-- unsatisfied with the security of this....

	case 'origin':
	    if (_proxy_jslib_instanceof(o, 'MessageEvent')) {
		if (o[property]==void 0) return void 0 ;
		if (o[property]=='*') return '*' ;
		return _proxy_jslib_parse_full_url(o[property])[2] ;
	    } else if (_proxy_jslib_instanceof(o, 'Location')) {
		var u= _proxy_jslib_parse_full_url(o.href.toString())[2] ;
		var pu= _proxy_jslib_parse_url(u) ;
		return pu[1] + '//' + pu[3] ;
	    } else {
		return _handle_default() ;
	    }

	case 'postMessage':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		return function(message, targetOrigin, ports) {
			   if ((targetOrigin=='*') || (targetOrigin=='/'))
			       return o.postMessage(message, targetOrigin, ports) ;

			   // security check-- targetOrigin must match o.location in scheme/host/port
			   var u= _proxy_jslib_parse_full_url(o.location.href)[2] ;
			   // jsm-- unless o.location is empty or about:blank?
			   if (u && u!='about:blank') {
			       var pu1= _proxy_jslib_parse_url(u) ;
			       var pu2= _proxy_jslib_parse_url(targetOrigin) ;
			       var port1= pu1[5] || (pu1[1]=='https'  ? 443  : 80) ;
			       var port2= pu2[5] || (pu2[1]=='https'  ? 443  : 80) ;
			       if ((pu1[1]!=pu2[1]) || (pu1[4]!=pu2[4]) || (port1!=port2))
				   return void 0 ;
			   }

			   targetOrigin= _proxy_jslib_full_url(targetOrigin) ;
			   return o.postMessage(message, targetOrigin, ports) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }


	case 'pushState':
	case 'replaceState':
	    if (_proxy_jslib_instanceof(o, 'History')) {
		return function(data, title, url) {
		    // url argument is optional
		    if (url==void 0) return o[property](data, title) ;

		    // must verify that origins of url and Document match!
		    var doc_pu= _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(document.URL)[2]) ;
		    var new_url= _proxy_jslib_full_url(url) ;
		    var o_pu= _proxy_jslib_parse_url(_proxy_jslib_parse_full_url(new_url)[2]) ;
		    if (o_pu[3]!=doc_pu[3]) {
			alert('History.'+property+'() not allowed unless origins match: ['+o_pu[3]+'] ['+doc_pu[3]+']') ;
			return void 0 ;
		    }
		    return o[property](data, title, _proxy_jslib_full_url(url)) ;
		}
	    } else {
		return _handle_default() ;
	    }


	case 'currentSrc':
	    if (_proxy_jslib_instanceof(o, 'MediaElement')) {
		return _proxy_jslib_parse_full_url(o[property])[2] ;
	    } else {
		return _handle_default() ;
	    }


	case 'importScripts':
	    if (_proxy_jslib_instanceof(o, 'WorkerGlobalScope')) {
		return function() {
		    var fakedoc= {URL: o.location} ;   // need this for _proxy_jslib_full_url() call
		    _proxy_jslib_set_base_vars(fakedoc) ;
		    for (var i= 0 ; i<arguments.length ; i++)
			o.importScripts(_proxy_jslib_full_url(arguments[i], fakedoc)) ;
		} ;
	    } else {
		return _handle_default() ;
	    }


	// Netscape-specific in this block
	case 'load':
	    if (_proxy_jslib_instanceof(o, 'Layer')) {
		if (!o.load) return undefined ;
		return function (url, width) {
			   if (this!==window) o= this ;
			   return o.load(_proxy_jslib_full_url(url), width) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }



	// MSIE-specific in this block

	case 'execScript':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		if (!o.execScript) return undefined ;
		return function(code, language) {
			   if (this!==window) o= this ;
			   if (language && language.match(/^\s*(javascript|jscript|ecmascript|livescript|$)/i))
			       return o.execScript(_proxy_jslib_proxify_js(code), language) ;
			   // either disallow or execute unchanged scripts we don't support
			   if (_proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS)
			       return o.execScript(code, language) ;
			   return ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'navigate':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		if (!o.navigate) return undefined ;
		return function (url) {
			   if (this!==window) o= this ;
			   return o.navigate(_proxy_jslib_full_url(url, o.document)) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'showModalDialog':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		if (!o.showModalDialog) return undefined ;
		return function(url, args, features) {
			   if (this!==window) o= this ;
			   return o.showModalDialog(_proxy_jslib_full_url(url, o.document), args, features) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }

	case 'showModelessDialog':
	    if (_proxy_jslib_instanceof(o, 'Window')) {
		if (!o.showModelessDialog) return undefined ;
		return function(url, args, features) {
			   if (this!==window) o= this ;
			   return o.showModelessDialog(_proxy_jslib_full_url(url, o.document), args, features) ;
		       } ;
	    } else {
		return _handle_default() ;
	    }


	// Document.execCommand() is a non-standard method supported by both
	//   MSIE and Firefox, though they support different sets of commands.
	// Note that values must be proxified relative to the calling Document
	//   object, not to the current document.
	case 'execCommand':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		return function (cmd, do_UI, value) {
			   var ret ;
//alert('in execCommand(); params=['+cmd+']['+do_UI+']['+value+']') ;  //jsm-- remove
			   cmd= cmd.toLowerCase() ;
			   if (_proxy_jslib_browser_family=='netscape') {
			       if ((cmd=='createlink') || (cmd=='insertimage')) {
				   ret= o.execCommand(cmd, do_UI, _proxy_jslib_full_url(value, o)) ;
			       } else if (cmd=='inserthtml') {
				   ret= o.execCommand(cmd, do_UI, _proxy_jslib_proxify_html(value, o)[0]) ;
			       } else {
				   ret= o.execCommand(cmd, do_UI, value) ;
			       }
			   } else if (_proxy_jslib_browser_family=='msie') {
			       if ((cmd=='createlink') || (cmd=='insertimage')) {
				   ret= o.execCommand(cmd, do_UI, _proxy_jslib_full_url(value, o)) ;
			       } else if (cmd.match(/^insert/)) {
				   alert('tried to execCommand('+cmd+')') ;
				   ret= undefined ;
			       } else {
				   ret= o.execCommand(cmd, do_UI, value) ;
			       }
			   }

			   return ret ;
		       } ;
	    } else {
		return _handle_default() ;
	    }



	// don't need to handle Document.parentWindow, do we?


	default:
	    return _handle_default() ;

    }




    // must be inside _proxy_jslib_handle() to retain o, property for closure
    function _handle_default() {

	if (calls_now && !in_new_statement && (typeof(o[property])=='function')) {
	    // Firefox (erroneously) reports that typeof(Function.prototype)
	    //   is 'function', not 'object' as it should be.
	    if (o==Function && property=='prototype') return o[property] ;

	    var fn= o[property] ;
	    var ret= function () {
			 // Handle "phantom functions"-- sometimes Firefox
			 //   seems to create Function objects with no
			 //   properties, where typeof=='function' but there
			 //   is no apply() method, where the constructor of
			 //   the function is undefined, and where
			 //   "fn instanceof Function" is false.  These were
			 //   causing CNN video controls to not work.  Oddly,
			 //   calling the phantom function with parameters
			 //   somehow makes it work-- does it alter a property
			 //   value, a flag, or what?  I don't know.
			 // Additionally, calling the function via eval does
			 //   not make it work, so we can't use the first
			 //   method below.  Possibly this is because of the
			 //   closure and the scope of o and property.  Also,
			 //   calling fn() doesn't make it work, even though
			 //   fn was set to o[property] .
			 if (fn.apply==void 0) {
			     // This doesn't work. :P
			     //var argst= '' ;
			     //for (var i= 0 ; i<arguments.length ; i++)
			     //    argst+= 'arguments['+i+'],' ;
			     //argst= argst.slice(0, -1) ;
			     //eval('return o[property]('+argst+')') ;

			     // lame!  will fail when arguments.length>10 .
			     return o[property](arguments[0], arguments[1],
						arguments[2], arguments[3],
						arguments[4], arguments[5],
						arguments[6], arguments[7],
						arguments[8], arguments[9]) ;
			 }

			 // Function.apply() not available in MSIE  :P
			 if (this!==window) {
			     return fn.apply(this, arguments) ;
			 } else {
			     return fn.apply(o, arguments) ;
			 }
		     } ;
	    // must copy all other properties too, in case anything's dereferenced
	    for (var p in o[property]) ret[p]= o[property][p] ;
	    return ret ;

	} else {
	    try {
		// hack for weird MSIE bug-- for some reason, it can't always
		//   access Element.getElementsByTagName() .
		if (_proxy_jslib_browser_family=='msie' && property=='getElementsByTagName')
		    return function(tagname) {
			       if (this!==window) o= this ;
			       return o.getElementsByTagName(tagname) ;
			   } ;

		return o[property] ;

	    } catch(e) {
//alert('in _handle_default() catch block; property=['+property+']; e=['+e+']') ;
		return undefined ;
	    }
	}

    }


}



// This is used when the property in question IS being assigned to, WITH an object.
function _proxy_jslib_assign (prefix, o, property, op, val) {
    var new_val ;

    // guess when the window object is implied
//    if ((o===null)  && (window[property]!==void 0) && (window[property]===cur_val)) o= window ;

    // handle prefix
    if (prefix=='delete') return delete o[property] ;
    if (prefix=='++') {
	val= o[property]+1 ;
	op= '=' ;
    } else if (prefix=='--') {
	val= o[property]-1 ;
	op= '=' ;
    }

// sanity check
//if (o==null) alert('in assign, o is null, property, caller=\n['+property+']\n['+arguments.callee.caller+']') ;   // jsm-- remove in production release?

    // performance tweak
    if (!_proxy_jslib_assign_props_hash['p_'+property]) return _assign_default() ;

    var opmod= op.match(/=/)  ? op.replace(/=$/, '')  : '' ;

    var fu, u ;
    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
	fu= _proxy_jslib_parse_full_url(o.href) ;
	u=  _proxy_jslib_parse_url(fu[2]) ;
    }
    // u[] has full_match, protocol, authentication, host, hostname, port, pathname, search, hash


    // For unknown object types, transform common URL properties such as "src".
    //   It's better to proxify a property too much than to open a privacy hole,
    //   which is what happens if such a property is a URL that does not get
    //   proxified.
    // Don't do this if the value it's being assigned to is a non-String object.
    //   This helps when variables have the same name as properties.
    // We don't cover all combinations of properties and operators here; e.g.
    //   URL-like properties are unlikely to use ++ or --, and other
    //   combinations don't usually make sense.  We can revisit if needed.
    // here we ignore case of "+=", etc.; revisit later if needed
    switch (property) {

	case 'src':
	case 'href':
	case 'lowsrc':
	case 'action':
	case 'formAction':
	case 'useMap':
	case 'longDesc':
	case 'cite':
	case 'codeBase':
	case 'location':
	case 'poster':
	    // Not sure what next two lines are needed for... need better comments!
	    //   But there are times o[property] is set to a non-String object, so remove them.
	    // // test if val is a non-String object
	    //if (!(val instanceof String) && !(typeof val=='string'))
	    // return eval('o[property]'+op+'val') ;

	    // don't convert if o is not a Node or a Location or a Window
	    if (!_proxy_jslib_instanceof(o, 'Node') && !_proxy_jslib_instanceof(o, 'Location') && !_proxy_jslib_instanceof(o, 'Window') )
		return eval('o[property]'+op+'val') ;
	    if (opmod!='') {
		new_val= _proxy_jslib_parse_full_url(o[property])[2] ;
		eval('new_val' + op + 'val') ;
	    } else {
		new_val= val ;
	    }
	    // this won't catch e.g. "top.location.href=u"... :P
	    if ((property=='location') && (o.top===o)) {
		o[property]= _proxy_jslib_full_url_by_frame(new_val, null, false) ;
	    } else {
		o[property]= _proxy_jslib_full_url(new_val, o.ownerDocument) ;
	    }
	    if (_proxy_jslib_instanceof(o, 'Window')) _proxy_jslib_init_domain(o) ;
	    // return unproxified value
	    return new_val ;

	case 'profile':
	    if (!o.tagName || o.tagName.toLowerCase()!='head')
		return o[property]= val ;
	    var u= val.split(/\s+/) ;
	    for (var i= 0 ; i<u.length ; i++)
		u[i]= _proxy_jslib_full_url(u[i], o.ownerDocument) ;
	    o[property]= u.join(' ') ;
	    return val ;

	case 'cssText':
	    o[property]= _proxy_jslib_proxify_css(val) ;
	    return val ;

	// these are properties of HTMLElement, i.e. could be one of many object types
	case 'innerHTML':
	case 'outerHTML':
	case 'outerText':
	    // only proxify it if the object is an HTMLElement or HTMLDocument
	    // MSIE has trouble with instanceof  :P
	    if (!_proxy_jslib_instanceof(o, 'HTMLElement') && !_proxy_jslib_instanceof(o, 'HTMLDocument'))
		return _assign_default() ;

	    // also avoid if it's in a script element, which jQuery uses
	    if (is_in_script(o, property))  return _assign_default() ;

	    // unproxify it first by calling _proxify_html() with reverse=true
	    if (op!='=') new_val= _proxy_jslib_proxify_html(o[property], (o.ownerDocument || o), false, true)[0] ;
	    eval('new_val' + op + 'val') ;
	    o[property]= _proxy_jslib_proxify_html(new_val, (o.ownerDocument || o), false)[0] ;
	    return new_val ;

	// same for properties of Node
	case 'nodeValue':
	    if (opmod!='') { eval('new_val= o[property]' + opmod + 'val') }
	    else           { new_val= val }
	    o[property]= _proxy_jslib_proxify_attribute(o, property, new_val) ;
	    return new_val ;


	// Various parts of Link and Location objects

	case 'protocol':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		o.href= _proxy_jslib_full_url(val+'//'+(u[2]!='' ? u[2]+'@' : '')+u[3]+u[6]+u[7]+u[8], o.ownerDocument) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }

	case 'host':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		o.href= _proxy_jslib_full_url(u[1]+'//'+(u[2]!='' ? u[2]+'@' : '')+val+u[6]+u[7]+u[8], o.ownerDocument) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }

	case 'hostname':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		o.href= _proxy_jslib_full_url(u[1]+'//'+(u[2]!='' ? u[2]+'@' : '')+val+(u[5]!='' ? ':'+u[5] : '')+u[6]+u[7]+u[8], o.ownerDocument) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }

	case 'port':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		o.href= _proxy_jslib_full_url(u[1]+'//'+(u[2]!='' ? u[2]+'@' : '')+u[4]+(val!='' ? ':'+val : '')+u[6]+u[7]+u[8], o.ownerDocument) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }

	case 'pathname':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		o.href= _proxy_jslib_full_url(u[1]+'//'+(u[2]!='' ? u[2]+'@' : '')+u[3]+val+u[7]+u[8], o.ownerDocument) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }

	case 'search':
	    if (_proxy_jslib_instanceof(o, 'Link') || _proxy_jslib_instanceof(o, 'Location')) {
		o.href= _proxy_jslib_full_url(u[1]+'//'+(u[2]!='' ? u[2]+'@' : '')+u[3]+u[6]+val+u[8], o.ownerDocument) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }


	case 'cookie':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		// simple way to test validity of cookie
		var new_cookie= _proxy_jslib_cookie_to_client(val) ;
		if (new_cookie=='') return '' ;
		if (_proxy_jslib_USE_DB_FOR_COOKIES) {
		    _proxy_jslib_store_cookie_in_db(val) ;
		    var c= val.match(/^\s*([^\=]+\=[^\;]*)/)[1] ;
		    if (c!=void 0) _proxy_jslib_COOKIES_FROM_DB+= ';' + c ;
		    return _proxy_jslib_COOKIES_FROM_DB ;
		}
		return o.cookie= new_cookie ;
	    } else {
		return _assign_default() ;
	    }

	// We store w._proxy_jslib_document_domain as "scheme://hostname:port",
	//   but Document.domain uses only hostname.
	case 'domain':
	    if (_proxy_jslib_instanceof(o, 'Document')) {
		var w= _proxy_jslib_doc2win(o) ;
		if (!w._proxy_jslib_document_domain) _proxy_jslib_init_domain(w) ;
		if (!w._proxy_jslib_document_domain) return ;  // unsupported scheme
		var pwurl= _proxy_jslib_parse_url(w._proxy_jslib_document_domain) ;
		var old_domain= pwurl[4] ;
		if (old_domain.match(/^[\d\.]+$/)) {
		    alert('Warning: tried to change document.domain from an IP address: ['+old_domain+']') ;
		    return ;
		}
		val= val.replace(/\.+$/, '') ;
		// new domain must be suffix of old domain, must contain a
		//   ".", and must be a complete domain suffix of old value
		//   (tested here by prefixing with "." before suffix check,
		//   but allowing if strings are equal).
		if ( ( (('.'+val)==old_domain.slice(-val.length-1))
		      || (val==old_domain) )
		    && val.match(/\./) )
			// since Document.domain only matches on hostname, use second line below.
			// return (w._proxy_jslib_document_domain= pwurl[1] + '//' + val + ':' + pwurl[5]) ;
			return (w._proxy_jslib_document_domain= 'http://' + val + ':80') ;
//		else alert('Warning: tried to set document.domain to illegal value: ['+val+'] existing domain: ['+w._proxy_jslib_document_domain+']') ;  // jsm
		break ;
	    } else {
		return _assign_default() ;
	    }



	// various CSS settings

	case 'value':
	    if (_proxy_jslib_instanceof(o, 'Attr')) {
		o.value= _proxy_jslib_proxify_attribute(o, o.name, val) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }


	case 'background':
	case 'backgroundImage':
	case 'content':
	case 'cursor':
	case 'listStyle':
	case 'listStyleImage':
	    if (_proxy_jslib_instanceof(o, 'CSS2Properties') || _proxy_jslib_instanceof(o, 'CSSStyleDeclaration')) {
		o[property]= _proxy_jslib_proxify_css(val) ;
		return val ;
	    } else {
		return _assign_default() ;
	    }


	case 'text':
	case 'textContent':
	    if (_proxy_jslib_instanceof(o, 'Node')) {
		if (o.nodeName.match(/^script$/i)) {
		    var type= o.type || _proxy_jslib_default_script_type ;
		    o[property]= _proxy_jslib_proxify_block(val, type,
			_proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, 0) ;
		    return val ;
		} else if (o.nodeName.match(/^style$/i)) {
		    var type= o.type || _proxy_jslib_default_style_type ;
		    o[property]= _proxy_jslib_proxify_block(val, type,
			_proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, 0) ;
		    return val ;
		} else {
		    return _assign_default() ;
		}

	    } else {
		return _assign_default() ;
	    }



	default:
	    return _assign_default() ;
    }


    function _assign_default() {
	if (op=='++') return o[property]++ ;
	else if (op=='--') return o[property]-- ;
	else if (op=='=') return o[property]= val ;   // optimization to not use eval
	else return eval('o[property]'+op+'val') ;
    }
}



// This is used when the property in question IS being assigned to, WITHOUT an object.
// The value returned is the value to set the variable to.
function _proxy_jslib_assign_rval (prefix, property, op, val, cur_val) {

    // handle prefix
    if (prefix=='delete') return undefined ;  // not quite the same as delete, but close enough?
    if (prefix=='++') {
	val= 1 ;
	op= '+=' ;
    } else if (prefix=='--') {
	val=  1 ;
	op= '-=' ;
    }

    if (val && (typeof val=='object') && (!('toLowerCase' in val)))
	return val ;
    var new_val= cur_val ;
    eval('new_val' + op + 'val') ;

    switch (property) {
	// when there's no object, "location" is the only property that needs proxification
	case 'location':
	    return _proxy_jslib_full_url(new_val) ;
	default:
	    return new_val ;
    }
}



// Next two routines are used when in a with() block.
function _proxy_jslib_with_handle (with_objs, property, cur_val, calls_now, in_new_statement) {
    for (var i= with_objs.length-1 ; i>=0 ; i--)
    if (property in with_objs[i])
	    return _proxy_jslib_handle(with_objs[i], property, with_objs[i][property], calls_now, in_new_statement) ;
    return _proxy_jslib_handle(null, property, cur_val, calls_now, in_new_statement) ;
}

function _proxy_jslib_with_assign_rval (with_objs, prefix, property, op, val, cur_val) {
    for (var i= with_objs.length-1 ; i>=0 ; i--)
    if (property in with_objs[i])
	return _proxy_jslib_assign(prefix, with_objs[i], property, op, val) ;
    return _proxy_jslib_assign_rval(prefix, property, op, val, cur_val) ;
}



//---- below are used to support the API functions above ---------------


// This is used for a test handling 'innerHTML' etc.
function is_in_script(el, property) {
    if (!_proxy_jslib_instanceof(el, 'HTMLElement')) return 0 ;
    var p= property=='innerHTML'  ? el  : el.parentNode ;
    while (p) {
	if (p.tagName=='SCRIPT') return 1 ;
	p= p.parentNode ;
    }
    return 0 ;
}


function _proxy_jslib_write_via_buffer(doc, html) {
    var i, buf ;
    for (i= 0 ; i<_proxy_jslib_write_buffers.length ; i++) {
	if (_proxy_jslib_write_buffers[i].doc===doc) {
	    buf= _proxy_jslib_write_buffers[i] ;
	    break ;
	}
    }
    if (!buf) {
	buf= _proxy_jslib_write_buffers[_proxy_jslib_write_buffers.length]=
	    { doc: doc, buf: html } ;
    } else {
	if (buf.buf==void 0) buf.buf= '' ;
	buf.buf+= html ;
    }
//    _proxy_jslib_flush_write_buffer(buf) ;
}


// careful-- output of document.write() may be (erroneously?) parsed and
//   executed immediately after document.write() statement.  To help with
//   that, we clear the buffer before calling document.write().
// Hack here for JS insertions-- if document was created and nothing written on
//   it yet, then insert the JS library if needed.
// Another hack-- since _proxy_jslib_write_buffers may be reset if what's
//   written includes jslib, we exit the loop if that happens.
function _proxy_jslib_flush_write_buffers() {
    var buf, i, p ;

    for (i= 0 ; (_proxy_jslib_write_buffers!=void 0) && (i<_proxy_jslib_write_buffers.length) ; i++) {
	buf= _proxy_jslib_write_buffers[i] ;
	if (buf.buf==void 0) continue ;
 
	p= _proxy_jslib_proxify_html(buf.buf, buf.doc, !buf.has_js) ;
	if (p[3]) return ;   // found frame document
//var w= _proxy_jslib_doc2win(buf.doc) ; if (w!=void 0) w= w.name ;
//if (confirm('flushing buffer;\nwin=['+w+']\nhas_js=['+p[2]+']\nout=['+p[0]+']')) ;
	buf.has_js= buf.has_js || p[2] ;
	buf.buf= p[1] ;
	buf.doc.write(p[0]) ;
    }
}


function _proxy_jslib_flush_write_buffer(buf) {
    var p= _proxy_jslib_proxify_html(buf.buf, buf.doc, !buf.has_js) ;
    if (p[3]) return ;   // found frame document
    buf.has_js= buf.has_js || p[2] ;
//alert('in flush; in=['+buf.buf+']\n\nout=['+p[0]+']\n\nremainder=['+p[1]+']') ;
    buf.buf= p[1] ;
    buf.doc.write(p[0]) ;
}




function _proxy_jslib_new_function() {
    arguments[arguments.length-1]= _proxy_jslib_proxify_js(arguments[arguments.length-1]) ;
    // MSIE 5.0 doesn't support Function.apply  :P
    return Function.apply(null, arguments) ;  // Function() same w/ or w/o "new"
}


function _proxy_jslib_doc2win(d) {
    return (_proxy_jslib_browser_family!='msie')
	? d.defaultView
	: d.parentWindow ;
}


// include fields needed for type ID, plus any other "authorized" fields.
function _proxy_jslib_dup_window_safe(w) {
    return { navigator:     w.navigator,
	     clearInterval: w.clearInterval,
	     moveBy:        w.moveBy,
	     self:          w,

	     location:      w.location,
	     postMessage:   function (message, targetOrigin, ports) {
				targetOrigin= _proxy_jslib_parse_full_url(targetOrigin)[2] ;
				return w.postMessage(message, targetOrigin, ports) ;
			    }
	   } ;
}


// Same-origin policy requires matching scheme, hostname, and port.
// This sets w._proxy_jslib_document_domain to "scheme://hostname:port", which
//   must be maintained.
// For about:blank pages, this sets w._proxy_jslib_document_domain to undefined.
// If the optional url parameter isn't provided, uses w.document.URL .
// Note that Document.domain only uses hostname; we accommodate this when getting
//   or setting it.
function _proxy_jslib_init_domain(w, url) {
    if (!url) {
	if (w.document.URL=='about:blank') {
	    w._proxy_jslib_document_domain= void 0 ;
	    return ;
	}
	url= w.document.URL.replace(/^wyciwyg:\/\/\d+\//i, '') ;
	url= _proxy_jslib_parse_full_url(url)[2] ;
	if (!url) return ;   // means on start page
	url= decodeURIComponent(url) ;
    }
    if (url=='about:blank') {
	w._proxy_jslib_document_domain= void 0 ;
	return ;
    }
    var purl= _proxy_jslib_parse_url(url) ;
    purl[3]= purl[3].replace(/\.+$/, '') ;
    if (!purl[5]) purl[5]= (purl[1]=='http:')   ? 80
			 : (purl[1]=='https:')  ? 443
			 :                        0 ;
    if (!purl[5]) w._proxy_jslib_document_domain= void 0 ;
    else w._proxy_jslib_document_domain= purl[1] + '//' + purl[3] + ':' + purl[5] ;
}


// Insert jslib and _proxy_jslib_pass_vars() call into an iframe.
// This is only needed for <iframe> elements with no src attribute.
// Must use document.write() to make insertion synchronous.
function _proxy_jslib_init_iframe(iframe) {
    var jslib_element= '<script src="' + _proxy_jslib_html_escape(_proxy_jslib_full_url('x-proxy://scripts/jslib')) + '" />' ;

    var base_url_jsq= document._proxy_jslib_base_url.replace(/(["\\\\])/g, function (p) { return "\\\\"+p } ) ;
    if (base_url_jsq!=void 0) base_url_jsq= '"' + base_url_jsq + '"' ;
    var cookies_from_db_jsq= _proxy_jslib_COOKIES_FROM_DB.replace(/(["\\\\])/g, function (p) { return "\\\\"+p } ) ;

    var pv_element= '<script>_proxy_jslib_pass_vars("' + base_url_jsq
		  + _proxy_jslib_cookies_are_banned_here + ','
		  + _proxy_jslib_doing_insert_here + ','
		  + _proxy_jslib_SESSION_COOKIES_ONLY + ','
		  + _proxy_jslib_COOKIE_PATH_FOLLOWS_SPEC + ','
		  + _proxy_jslib_RESPECT_THREE_DOT_RULE + ','
		  + _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS + ',"'
		  + _proxy_jslib_RTMP_SERVER_PORT + '","'
		  + _proxy_jslib_default_script_type + '","'
		  + _proxy_jslib_default_style_type + '",'
		  + _proxy_jslib_USE_DB_FOR_COOKIES + ',"'
		  + cookies_from_db_jsq + '")<\/script>' ;

    iframe.contentDocument.write(jslib_element + pv_element) ;
}




// returns proxified URL, relative to doc
function _proxy_jslib_full_url(uri_ref, doc, reverse, retain_query) {
    var script, r_l, m1, m2, r_q, query,
	data_type, data_clauses, data_content, data_charset, data_base64 ;

    if (!uri_ref) return uri_ref ;

    // Hack to prevent double-proxified URLs in SWFs, meaning we can't chain
    //   through the same script location.
    if (!reverse && (uri_ref.toString().slice(0, _proxy_jslib_url_start.length)==_proxy_jslib_url_start))
	return uri_ref ;

    // Apparently some non-string objects are passed here... Location? Link?
    uri_ref= uri_ref.toString() ;

    // Disable retain_query until potential anonymity issues are resolved.
    retain_query= false ;

    // hack for my.yahoo.com; it creates the non-functional src="//:" on purpose (?)
    if (uri_ref=='//:') return uri_ref ;

    if (!doc) doc= window.document ;

//if (uri_ref==null) alert('null; caller=['+arguments.callee.caller+']') ;  // caller==null
//if (uri_ref.match(/\/[01]{6}[A-Z]\//)) alert('in full_url; uri_ref, caller=\n['+uri_ref+']\n['+arguments.callee.caller+']') ;   // jsm
    if (uri_ref==null) return '' ;
    if (reverse) return _proxy_jslib_parse_full_url(uri_ref)[2] ;

    if (!doc._proxy_jslib_base_url) _proxy_jslib_set_base_vars(doc, _proxy_jslib_parse_full_url(doc.URL)[2]) ;

    uri_ref= uri_ref.replace(/^\s+|\s+$/g, '') ;
    if (/^x\-proxy\:\/\//i.test(uri_ref))  return '' ;
    if (uri_ref.match(/^about\:\s*blank$/i))  return uri_ref ;

    if (/^(javascript|livescript)\:/i.test(uri_ref)) {
	script= uri_ref.replace(/^(javascript|livescript)\:/i, '') ;
	r_l= _proxy_jslib_separate_last_js_statement(script) ;
	r_l[1]= r_l[1].replace(/\s*;\s*$/, '') ;
	return 'javascript:' + _proxy_jslib_proxify_js(r_l[0], 1)
			     + '; _proxy_jslib_proxify_html(' + _proxy_jslib_proxify_js(r_l[1], 0) + ')[0]' ;

    // The "FSCommand:" URL may be called by Flash apps.
    } else if (m1= uri_ref.match(/^(fscommand:)(.*)/i)) {
	return m1[1] + _proxy_jslib_proxify_js(m1[2]) ;
    
    } else if (m1= uri_ref.match(/^data:([\w\.\+\$\-]+\/[\w\.\+\$\-]+)?;?([^\,]*)\,?(.*)/i)) {
	data_type= m1[1].toLowerCase() ;
	if (data_type=='text/html' || data_type=='text/css' || data_type.match(/script/i)) {
	    data_clauses= m1[2].split(/;/) ;
	    data_content= m1[3] ;
	    for (var i= 0 ; i<data_clauses.length ; i++) {
		if (m2= data_clauses[i].match(/^charset=(\S+)/i)) {
		    data_charset= m2[1] ;
		} else if (data_clauses[i].toLowerCase()=='base64') {
		    data_base64= 1 ;
		}
	    }
	    data_content= data_base64
			? atob(data_content)
			: data_content.replace(/%([\da-fA-F]{2})/g,
			  function (s,p1) { return String.fromCharCode(eval('0x'+p1)) } ) ;   // probably slow
	    data_content= (data_type=='text/html')  ? _proxy_jslib_proxify_html(data_content)
						    : _proxy_jslib_proxify_block(data_content, data_type, 1) ;
	    data_content= btoa(data_content) ;
	    return data_charset  ? 'data:' + data_type + ';charset=' + data_charset + ';base64,' + data_content
				 : 'data:' + data_type + ';base64,' + data_content ;
	} else {
	    return uri_ref ;
	}
    }

    var uf= uri_ref.match(/^([^\#]*)(\#.*)?/) ;
    var uri= uf[1] ;
    var frag=  uf[2]  ? uf[2]  : '' ;
    if (uri=='')  return uri_ref ;

    uri= uri.replace(/[\r\n]/g, '') ;

    if (retain_query) {
	r_q= uri.split(/\?/) ;
	uri= r_q[0] ;
	query= r_q[1] ;
	if (query) query= '?'+query ;
	else query= '' ;
    }

    var absurl ;
    if      (/^[\w\+\.\-]*\:/.test(uri))  { absurl= uri               }
    else if (/^\/\//.test(uri))           { absurl= doc._proxy_jslib_base_scheme + uri }
    else if (/^\//.test(uri))             { absurl= doc._proxy_jslib_base_host   + uri }
    else if (/^\?/.test(uri))             { absurl= doc._proxy_jslib_base_file   + uri }
    else                                  { absurl= doc._proxy_jslib_base_path   + uri }

    var ret= _proxy_jslib_url_start + _proxy_jslib_wrap_proxy_encode(absurl) + (retain_query ? query : '') + frag ;
    return ret ;
}


function _proxy_jslib_full_url_by_frame(uri_ref, doc, is_frame, reverse) {
    var old_url_start= _proxy_jslib_url_start ;
    _proxy_jslib_url_start= is_frame  ? _proxy_jslib_url_start_inframe  : _proxy_jslib_url_start_noframe ;
    var ret= _proxy_jslib_full_url(uri_ref, doc, reverse) ;
    _proxy_jslib_url_start= old_url_start ;
    return ret ;
}


// initializes _base vars for the given document
function _proxy_jslib_set_base_vars(doc, base_url) {
    if (!base_url) base_url= doc.URL ;
    doc._proxy_jslib_base_url= base_url.replace(/^\s+|\s+$/g, '')
				       .replace(/^([\w\+\.\-]+\:\/\/[^\/\?]+)\/?/, "$1/") ;
    if (!base_url.match(/^\s*https?\:\/\//i)) return ; // handles "about:blank", etc.
    doc._proxy_jslib_base_scheme= doc._proxy_jslib_base_url.match(/^([\w\+\.\-]+\:)\/\//)[1] ;
    doc._proxy_jslib_base_host=   doc._proxy_jslib_base_url.match(/^([\w\+\.\-]+\:\/\/[^\/\?]+)/)[1] ;
    doc._proxy_jslib_base_path=   doc._proxy_jslib_base_url.match(/^([^\?]*\/)/)[1] ;
    doc._proxy_jslib_base_file=   doc._proxy_jslib_base_url.match(/^([^\?]*)/)[1] ;
}




function _proxy_jslib_wrap_proxy_encode(URL) {
    var uf= URL.match(/^([^\#]*)(\#.*)?/) ;
    var uri= uf[1] ;
    var frag=  uf[2]  ? uf[2]  : '' ;

    uri= _proxy_jslib_proxy_encode(uri) ;
    uri= uri.replace(/\=/g, '=3d').replace(/\?/g, '=3f').replace(/\#/g, '=23')
	    .replace(/\%/g, '=25').replace(/\&/g, '=26').replace(/\;/g, '=3b') ;
    while (uri.match(/\/\//)) uri= uri.replace(/\/\//g, '/=2f') ;

    return uri + frag ;
}

function _proxy_jslib_wrap_proxy_decode(enc_URL) {
    var uf= enc_URL.match(/^([^\?\#]*)([^\#]*)(.*)/) ;
    var uri= uf[1] ;
    var query= uf[2] ;
    var frag=  uf[3]  ? uf[3]  : '' ;

    // Unfortunately, this little function turns out to be a CPU hog
    //uri= uri.replace(/\=(..)/g, function (s,p1) { return String.fromCharCode(eval('0x'+p1)) } ) ;
    uri= uri.replace(/\=2f/g, '/').replace(/\=25/g, '%').replace(/\=23/g, '#')
	    .replace(/\=3f/g, '?').replace(/\=26/g, '&').replace(/\=3b/g, ';')
	    .replace(/\=3d/g, '=') ;
    uri= _proxy_jslib_proxy_decode(uri) ;

    return uri + query + frag ;
}


// Next two functions for Flash 9+ support.
function _proxy_jslib_full_url_connect(url) {
    var m ;
//alert('starting _proxy_jslib_full_url_connect('+url+'), typeof=['+(typeof url)+']') ;
    if (!url) return url ;
    if (url.match(/^https?\:\/\//i)) return _proxy_jslib_full_url(url) ;
    if (m= url.match(/^rtmp\:\/\/([^\/]*\/[^\/]*)\/(.*)/i)) {
	var new_app= encodeURIComponent(m[1]) ;  // not perfect, but good for now?
	var portst= _proxy_jslib_RTMP_SERVER_PORT==1935  ? ''  : ':' + _proxy_jslib_RTMP_SERVER_PORT ;
	return 'rtmp://' + _proxy_jslib_THIS_HOST + portst + '/' + new_app + '/' + m[2] ;
    }
    return url ;
}

function _proxy_jslib_full_url_play(url) {
//alert('starting _proxy_jslib_full_url_play('+url+'), typeof=['+(typeof url)+']') ;
    if (!url) return url ;
    if (typeof url!='string') return url ;    // in case called for wrong 'play'
    if (!url.match(/^https?\:\/\//i)) return url ;
    return _proxy_jslib_full_url(url) ;   // could use retain_query param when supported
}

// simple function for Flash to call, for e.g. flash.display.LoaderInfo.loaderURL
function _proxy_jslib_reverse_full_url(url) {
    return _proxy_jslib_parse_full_url(url)[2] ;
}



function _proxy_jslib_cookie_to_client(cookie) {
    if (_proxy_jslib_cookies_are_banned_here) return '' ;

    var u= _proxy_jslib_parse_url(_proxy_jslib_URL) ;
    if (u==null) {
	alert("CGIProxy Error: Can't parse URL <"+_proxy_jslib_URL+">; not setting cookie.") ;
	return '' ;
    }
    var source_server= u[4] ;
    var source_path= u[6] ;
    if (source_path.substr(0,1)!='/') source_path= '/' + source_path ;

    cookie= cookie.replace(/[\0\n\r]/g, '') ;    // prevent HTTP header injection

    var name, value, expires_clause, path, domain, secure_clause ;
    var new_name, new_value, new_cookie ;

    name= value= expires_clause= path= domain= secure_clause=
	new_name= new_value= new_cookie= '' ;

    if (/^\s*([^\=\;\,\s]*)\s*\=?\s*([^\;]*)/.test(cookie)) {
	name= RegExp.$1 ; value= RegExp.$2 ;
    }
    if (/\;\s*(expires\s*\=[^\;]*)/i.test(cookie))        expires_clause= RegExp.$1 ;
    if (/\;\s*path\s*\=\s*([^\;\,\s]*)/i.test(cookie))    path= RegExp.$1 ;
    if (/\;\s*domain\s*\=\s*([^\;\,\s]*)/i.test(cookie))  domain= RegExp.$1 ;
    if (/\;\s*(secure\b)/i.test(cookie))                  secure_clause= RegExp.$1 ;

    if (path=='') path= _proxy_jslib_COOKIE_PATH_FOLLOWS_SPEC  ? source_path  : '/' ;

    if (domain=='') {
	domain= source_server ;
    } else {
	domain= domain.replace(/\.+$/, '') ;
	domain= domain.replace(/\.{2,}/g, '.') ;
	if ( (source_server.substr(source_server.length-domain.length)!=domain.toLowerCase()) && ('.'+source_server!=domain) )
	    return '' ;
	if (domain.match(/^[\d\.]$/) && (domain!=source_server))  return '' ;   // illegal to use partial IP address
	var dots= domain.match(/\./g) ;
	if (_proxy_jslib_RESPECT_THREE_DOT_RULE) {
	    if (dots.length<3 && !( dots.length>=2 && /\.(com|edu|net|org|gov|mil|int)$/i.test(domain) ) )
		return '' ;
	} else {
	    if (dots.length<2) {
		if (domain.match(/^\./)) return '' ;
		domain= '.'+domain ;
		if (dots.length<1) return '' ;
	    }
	}
    }

    new_name=  _proxy_jslib_cookie_encode('COOKIE;'+name+';'+path+';'+domain) ;
    new_value= _proxy_jslib_cookie_encode(value+';'+secure_clause) ;

    if (_proxy_jslib_SESSION_COOKIES_ONLY && (expires_clause!='')) {
	/^expires\s*\=\s*(.*)$/i.test(expires_clause) ;
	var expires_date= RegExp.$1.replace(/\-/g, ' ') ;  // Date.parse() can't handle "-"
	if ( Date.parse(expires_date) > (new Date()).getTime() ) expires_clause= '' ;
    }

    new_cookie= new_name+'='+new_value ;
    if (expires_clause!='') new_cookie= new_cookie+'; '+expires_clause ;
    new_cookie= new_cookie+'; path='+_proxy_jslib_SCRIPT_NAME+'/' ;
//    if (secure_clause!='')  new_cookie= new_cookie+'; '+secure_clause ;

    return new_cookie ;
}


function _proxy_jslib_cookie_from_client(doc) {
    if (_proxy_jslib_cookies_are_banned_here) return _proxy_jslib_COOKIES_FROM_DB ;
    if (!doc.cookie) return _proxy_jslib_COOKIES_FROM_DB ;

    var target_path, target_server, target_scheme ;
    var u= _proxy_jslib_parse_url(_proxy_jslib_URL) ;
    if (u==null) {
	alert("CGIProxy Error: Can't parse URL <"+_proxy_jslib_URL+">; not using cookie.") ;
	return ;
    }
    target_scheme= u[1] ;
    target_server= u[4] ;
    target_path= u[6] ;
    if (target_path.substr(0,1)!='/') target_path= '/' + target_path ;

    var matches= new Array() ;
    var pathlen= new Object() ;
    var cookies= doc.cookie.split(/\s*;\s*/) ;
    //for (var c in cookies) {
    for (var c= 0 ; c < cookies.length ; c++) {
	var nv= cookies[c].split('=', 2) ;
	var name=  _proxy_jslib_cookie_decode(nv[0]) ;
	var value= _proxy_jslib_cookie_decode(nv[1]) ;
	var n= name.split(/;/) ;
	if (n[0]=='COOKIE') {
	    var cname, path, domain, cvalue, secure ;
	    cname= n[1] ; path= n[2] ; domain= n[3].toLowerCase() ;
	    var v= value.split(/;/) ;
	    cvalue= v[0] ; secure= v[1] ;
	    if (secure!='' && secure!=null && target_scheme!='https:') continue ;
	    if ( ((target_server.substr(target_server.length-domain.length)==domain)
		  || (domain=='.'+target_server))
		&& target_path.substr(0, path.length)==path )
	    {
		matches[matches.length]= cname  ? cname+'='+cvalue  : cvalue ;
		pathlen[cname+'='+cvalue]= path.length ;
	    }
	}
    }

    matches.sort(function (v1,v2) { return (pathlen[v2]-pathlen[v1]) } ) ;

    if (_proxy_jslib_COOKIES_FROM_DB!='') matches.unshift(_proxy_jslib_COOKIES_FROM_DB) ;

    return matches.join('; ') ;
}


// this doesn't need to process a response
function _proxy_jslib_store_cookie_in_db(cookie) {
    var url= _proxy_jslib_full_url('x-proxy://cookies/set-cookie?'+_proxy_jslib_cookie_encode(cookie)) ;
    var xhr= new XMLHttpRequest() ;
    xhr.open('GET', url) ;
    xhr.send() ;
}




// returns [new_html, remainder, jslib_added, found_frameset]
// call with reverse=true to un-proxify a block of HTML-- convenient but kinda hacky
function _proxy_jslib_proxify_html(html, doc, is_full_page, reverse) {
    var out= [] ;
    var match, m2, last_lastIndex= 0, remainder ;
    var tag_name, html_pos, head_pos ;
    var base_url, base_url_jsq, jslib_block, insert_string, insert_pos ;
    var jslib_added= false ;

    if (html==void 0) return [void 0, void 0, false, false] ;
    if (typeof html=='number') return [html, void 0, false, false] ;

    if (is_full_page) _proxy_jslib_needs_jslib= false ;


    // start, comment, script_block, style_block, decl_bang, decl_question, tag
    // note that a unique instance of RE must be created, in case of recursion
    var RE= new RegExp(/([^\<]*(?:\<(?![\w\/])[^\<]*)*)(?:(\<\!\-\-(?=[\s\S]*?\-\-\>)[\s\S]*?\-\-\s*\>|\<\!\-\-(?![\s\S]*?\-\-\>)[\s\S]*?\>)|(\<script\b[\s\S]*?\<\/script\b[\s\S]*?\>)|(\<style\b[\s\S]*?\<\/style\b[\s\S]*?\>)|(\<\![^\>]*\>)|(\<\?[^\>]*\>)|(\<[^\>]*\>))?/gi) ;
    var RE2= new RegExp(/[^\>]*(?:\>|$)/g) ;

    while ((last_lastIndex!=html.length) && (match= RE.exec(html))) {
	if (match.index!=last_lastIndex) {
	    remainder= html.slice(last_lastIndex) ;
	    break ;
	}
	last_lastIndex= RE2.lastIndex= RE.lastIndex ;

	out.push(match[1]) ;

	if (match[2]) {
	    out.push(_proxy_jslib_proxify_comment(match[2], doc, reverse)) ;
	} else if (match[3]) {
	    out.push(_proxy_jslib_proxify_script_block(match[3], doc, reverse)) ;
	} else if (match[4]) {
	    out.push(_proxy_jslib_proxify_style_block(match[4], doc, reverse)) ;
	} else if (match[5]) {
	    out.push(_proxy_jslib_proxify_decl_bang(match[5], doc, reverse)) ;
	} else if (match[6]) {
	    out.push(_proxy_jslib_proxify_decl_question(match[6], doc, reverse)) ;

	} else if (match[7]) {
	    m2= match[7].match(/^\<\s*(\/?[A-Za-z][\w\.\:\-]*)/) ;
if (!m2) alert('no m2; match[7]=['+match[7]+']') ;
	    tag_name= m2[1].toLowerCase() ;

	    // these would indicate incomplete blocks
	    if ((tag_name=='script') || (tag_name=='style')) {
		remainder= match[7]+html.slice(last_lastIndex) ;
		break ;
	    }

	    if ((tag_name=='frameset') && _proxy_jslib_doing_insert_here && !_proxy_jslib_is_in_frame && !reverse) {
		_proxy_jslib_return_frame_doc(_proxy_jslib_wrap_proxy_encode(_proxy_jslib_URL), doc) ;
		return ['', void 0, false, true] ;
	    }

	    if (tag_name=='/object') _proxy_jslib_current_object_classid= '' ;

	    // if undefined return value, add up to next ">" and try again
	    var new_element= _proxy_jslib_proxify_element(match[7], doc, reverse) ;
	    while (new_element==void 0 && last_lastIndex!=html.length) {
		m2= RE2.exec(html) ;
		last_lastIndex= RE.lastIndex= RE2.lastIndex ;
		match[7]+= m2[0] ;
		new_element= _proxy_jslib_proxify_element(match[7], doc, reverse) ;
	    }
	    out.push(new_element) ;

	    if      (tag_name=='html') { html_pos= out.length }
	    else if (tag_name=='head') { head_pos= out.length }
	}
    }

    if ((last_lastIndex!=html.length) && !remainder)
	 remainder= html.slice(last_lastIndex) ;


    if (reverse) _proxy_jslib_needs_jslib= false ;

    // Don't worry about top insertion.  Hacky.
    if (is_full_page && _proxy_jslib_needs_jslib && !reverse) {

	jslib_block= '<script type="text/javascript" src="'
		       + _proxy_jslib_html_escape(_proxy_jslib_url_start+_proxy_jslib_wrap_proxy_encode('x-proxy://scripts/jslib'))
		       + '"><\/script>\n' ;

	if (!doc._proxy_jslib_base_url) {
	    base_url= _proxy_jslib_parse_full_url(doc.URL)[2] ;
	    _proxy_jslib_set_base_vars(doc, base_url) ;
	}
	base_url_jsq= doc._proxy_jslib_base_url
		.replace(/(["\\])/g, function (p) { return '\\'+p } ) ;
	if (base_url_jsq!=void 0) base_url_jsq= '"' + base_url_jsq + '"' ;
	var cookies_from_db_jsq= _proxy_jslib_COOKIES_FROM_DB.replace(/(["\\\\])/g, function (p) { return "\\\\"+p } ) ;
	insert_string= '<script type="text/javascript">_proxy_jslib_pass_vars('
		     + base_url_jsq + ','
		     + _proxy_jslib_cookies_are_banned_here + ','
		     + _proxy_jslib_doing_insert_here + ','
		     + _proxy_jslib_SESSION_COOKIES_ONLY + ','
		     + _proxy_jslib_COOKIE_PATH_FOLLOWS_SPEC + ','
		     + _proxy_jslib_RESPECT_THREE_DOT_RULE + ','
		     + _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS + ',"'
		     + _proxy_jslib_RTMP_SERVER_PORT + '","'
		     + _proxy_jslib_default_script_type + '","'
		     + _proxy_jslib_default_style_type + '",'
		     + _proxy_jslib_USE_DB_FOR_COOKIES + ',"'
		     + cookies_from_db_jsq + '");<\/script>\n' ;
	insert_pos= head_pos || html_pos || 0 ;
	out.splice(insert_pos, 0, jslib_block, insert_string) ;
	jslib_added= true ;
    }

    return [out.join(''), remainder, jslib_added] ;
}



function _proxy_jslib_proxify_comment(comment, doc, reverse) {
    var m= comment.match(/^\<\!\-\-(.*?)(\-\-\s*)?>$/) ;
    var contents= m[1] ;
    var end= m[2] ;
    contents= _proxy_jslib_proxify_html(contents, doc, false, reverse)[0] ;
    comment= '<!--' + contents + end + '>' ;
    return comment ;
}


function _proxy_jslib_proxify_decl_bang(decl_bang, doc, reverse) {
    var q ;
    var inside= decl_bang.match(/^\<\!([^>]*)/)[1] ;
    var words= inside.match(/\"[^\"\>]*\"?|\'[^\'\>]*\'?|[^\'\"][^\s\>]*/g) ;
    for (var i=0 ; i<words.length ; i++) {
	words[i]= words[i].replace(/^\s*/, '') ;
	if (words[i].match(/^[\'\"]?http\:\/\/www\.w3\.org\//)) continue ;
	if (words[i].match(/^[\"\']?[\w\+\.\-]+\:\/\//)) {
	    if      (words[i].match(/^'/))  { q= "'" ; words[i]= words[i].replace(/^\'|\'$/g, '') }
	    else if (words[i].match(/^"/))  { q= '"' ; words[i]= words[i].replace(/^\"|\"$/g, '') }
	    else                            { q= '' }
	    words[i]= q + _proxy_jslib_full_url(words[i], doc, reverse) + q ;
	}
    }
    decl_bang= '<!' + words.join(' ') + '>' ;
    return decl_bang ;
}


function _proxy_jslib_proxify_decl_question(decl_question, doc, reverse) {
    return decl_question ;
}


function _proxy_jslib_proxify_script_block(script_block, doc, reverse) {
    var m1, m2, tag, script, attrs, attr, name ;
    attr= new Object() ;

    m1= script_block.match(/^(\<\s*script\b[^\>]*\>)([\s\S]*)\<\s*\/script\b[^\>]*\>$/i) ;
    var o_n_j= _proxy_jslib_needs_jslib ;   // hack hack
    tag= _proxy_jslib_proxify_element(m1[1], doc, reverse) ;
    _proxy_jslib_needs_jslib= o_n_j ;
    script= m1[2] ;
    attrs= tag.match(/^\<\s*script\b([^\>]*)\>/i)[1] ;

    while (m2= attrs.match(/([A-Za-z][\w\.\:\-]*)\s*(\=\s*(\"([^\"\>]*)\"?|\'([^\'\>]*)\'?|([^\'\"][^\s\>]*)))?/)) {
	attrs= attrs.substr(m2[0].length) ;
	name= m2[1].toLowerCase() ;
	if (attr[name]!=null) continue ;
	attr[name]= m2[4]  ? m2[4]  : m2[5]  ? m2[5]  : m2[6]  ? m2[6]  : '' ;
	attr[name]= _proxy_jslib_html_unescape(attr[name]) ;
    }
    if (attr.type!=null) attr.type= attr.type.toLowerCase() ;
    if (!attr.type && attr.language) {
	attr.type= attr.language.match(/javascript|ecmascript|livescript|jscript/i)
						     ? 'application/x-javascript'
		 : attr.language.match(/css/i)       ? 'text/css'
		 : attr.language.match(/vbscript/i)  ? 'application/x-vbscript'
		 : attr.language.match(/perl/i)      ? 'application/x-perlscript'
		 : attr.language.match(/tcl/i)       ? 'text/tcl'
		 : '' ;
    }
    if (!attr.type) attr.type= _proxy_jslib_default_script_type ;

    // For now, don't worry about "<\/script" (unescaped) inside JS-written scripts.

    script= _proxy_jslib_proxify_block(script, attr.type,
		_proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, reverse) ;

    return tag+script+'<\/script>' ;
}


function _proxy_jslib_proxify_style_block(style_block, doc, reverse) {
    var m1, m2, tag, stylesheet, attrs, type ;
    m1= style_block.match(/^(\<\s*style\b[^\>]*\>)([\s\S]*)\<\s*\/style\b[^\>]*\>$/i) ;
    var o_n_j= _proxy_jslib_needs_jslib ;   // hack hack
    tag= _proxy_jslib_proxify_element(m1[1], doc, reverse) ;
    _proxy_jslib_needs_jslib= o_n_j ;
    stylesheet= m1[2] ;
    attrs= tag.match(/^\<\s*style\b([^\>]*)\>/i)[1] ;

    while (m2= attrs.match(/([A-Za-z][\w\.\:\-]*)\s*(\=\s*(\"([^\"\>]*)\"?|\'([^\'\>]*)\'?|([^\'\"][^\s\>]*)))?/)) {
	attrs= attrs.substr(m2[0].length) ;
	if (m2[1].toLowerCase()=='type') {
	    type= m2[4]!=null  ? m2[4]  : m2[5]!=null  ? m2[5]  : m2[6]!=null  ? m2[6]  : '' ;
	    type= _proxy_jslib_html_unescape(type).toLowerCase() ;
	    break ;
	}
    }
    if (!type) type= _proxy_jslib_default_style_type ;
    stylesheet= _proxy_jslib_proxify_block(stylesheet, type,
			_proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, reverse) ;

    return tag+stylesheet+'<\/style>' ;
}



// returns undef on error, like when "<>" are in an attribute (hacky)
function _proxy_jslib_proxify_element(element, doc, reverse) {
    // Unfortunately, attr{} may have extra properties if a Web page changes
    //   anything in the Object prototype.  Thus, we use names[] to keep track
    //   of the tag's attributes.  We do this elsewhere too.
    var m1, m2, tag_name, attrs, attr= {}, names= [], name, i, rebuild, end_slash,
	old_url_start, flags ;
    if (!doc) doc= window.document ;

    if (!(m1= element.match(/^\<\s*([A-Za-z][\w\.\:\-]*)\s*([\s\S]*)$/))) return element ;
    tag_name= m1[1].toLowerCase() ;
    attrs= m1[2] ;
    // ignore possibility of <frameset> tag
    if (attrs=='') return element ;

    // note that last match indicates an unterminated string
    while (m2= attrs.match(/([A-Za-z][\w\.\:\-]*)\s*(\=\s*(\"([^\"]*)\"|\'([^\']*)\'|([^\'\"][^\s\>]*)|(\'[^\']*$|\"[^\"]*$)))?/)) {
	// if ends on broken string, return undef
	if (m2[7]) return void 0 ;
	attrs= attrs.substr(m2.index+m2[0].length) ;
	name= m2[1].toLowerCase() ;
	if (name in attr) { rebuild= 1 ; continue }
	// must compare to both undefined and '' to cover all browsers
	attr[name]= (m2[4]!=void 0 && m2[4]!='') ? m2[4]
		  : (m2[5]!=void 0 && m2[5]!='') ? m2[5]
		  : (m2[6]!=void 0 && m2[6]!='') ? m2[6]
		  : '' ;
	attr[name]= _proxy_jslib_html_unescape(attr[name]) ;
	names.push(name) ;
    }


    // Now we have tag_name, attr[], and names[] set.

//    for (name in attr) {
    for (i= 0 ; i<names.length ; i++) {
	name= names[i] ;
	// for now, simply delete attributes with script macros
	if (attr[name].match(/\&\{.*\}\;/)) { delete attr[name] ; rebuild= 1 ; continue }

	if (name.match(/^on/)) {
	    attr[name]= _proxy_jslib_proxify_block(attr[name], _proxy_jslib_default_script_type, _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, reverse) ;
	    rebuild= 1 ;
	}
    }


    if (tag_name=='object') {
	_proxy_jslib_current_object_classid= attr.classid ;
	if (attr.data) {
	    var old_url_start= _proxy_jslib_url_start ;
	    var flags= _proxy_jslib_unpack_flags(_proxy_jslib_packed_flags) ;
	    flags[5]= 1 ;
	    _proxy_jslib_url_start= _proxy_jslib_SCRIPT_URL + '/' + _proxy_jslib_pack_flags(flags) + '/' ;
	    attr.data= _proxy_jslib_full_url(attr.data, doc, reverse) ;
	    _proxy_jslib_url_start= old_url_start ;
	    rebuild= 1 ;
	}

    } else if (tag_name=='param') {
//	if (_proxy_jslib_current_object_classid &&
//	    _proxy_jslib_current_object_classid.match(/^\s*clsid\:\{?D27CDB6E-AE6D-11CF-96B8-444553540000\}?\s*$/i))
//	{
	    if (attr.name && attr.name.match(/^movie$/i)) {
		attr.value= _proxy_jslib_full_url(attr.value, doc, reverse, 1) ;
		rebuild= 1 ;
	    }
//	}
    }


    if ('style' in attr) {
	if (attr.style.match(/(expression|function)\s*\(/i ))
	    attr.style= _proxy_jslib_global_replace(attr.style, /\b((expression|function)\s*\()([^\)]*)/i,
						    function (p) { return p[1]+_proxy_jslib_proxify_js(p[3], void 0, void 0, void 0, reverse) } ) ;

	attr.style= _proxy_jslib_proxify_block(attr.style, _proxy_jslib_default_style_type, _proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, reverse) ;
	rebuild= 1 ;
    }

    // huge simplification of tag-specific block
    if ('href' in attr)        { attr.href=        _proxy_jslib_full_url(attr.href, doc, reverse) ;        rebuild= 1 }
    if ('src' in attr)         {
	if (tag_name=='frame' || tag_name=='iframe') {
				 attr.src=         _proxy_jslib_full_url_by_frame(attr.src, doc, 1, reverse) ; rebuild= 1 ;
	} else if (tag_name=='script') {   // messy  :P
	    var old_url_start= _proxy_jslib_url_start ;
	    var flags= _proxy_jslib_unpack_flags(_proxy_jslib_packed_flags) ;
	    flags[6]= (attr.type!==void 0)  ? attr.type  : _proxy_jslib_default_script_type ;
	    _proxy_jslib_url_start= _proxy_jslib_SCRIPT_URL + '/' + _proxy_jslib_pack_flags(flags) + '/' ;
				 attr.src=         _proxy_jslib_full_url(attr.src, doc, reverse) ;         rebuild= 1 ;
	    _proxy_jslib_needs_jslib= true ;
	    _proxy_jslib_url_start= old_url_start ;
	} else if (tag_name=='embed') {
			       { attr.src=         _proxy_jslib_full_url(attr.src, doc, reverse, (attr.type && attr.type.toLowerCase()=='application/x-shockwave-flash')) ;      rebuild= 1 }
	} else                 { attr.src=         _proxy_jslib_full_url(attr.src, doc, reverse) ;         rebuild= 1 }
    }
    if ('srcdoc' in attr)      {
	if (tag_name=='iframe')  attr.srcdoc=      _proxy_jslib_proxify_html(attr.srcdoc, doc, 1, reverse) ; rebuild= 1 }
    if ('lowsrc' in attr)      { attr.lowsrc=      _proxy_jslib_full_url(attr.lowsrc, doc, reverse) ;      rebuild= 1 }
    if ('dynsrc' in attr)      { attr.dynsrc=      _proxy_jslib_full_url(attr.dynsrc, doc, reverse) ;      rebuild= 1 }
    if ('action' in attr)      { attr.action=      _proxy_jslib_full_url(attr.action, doc, reverse) ;      rebuild= 1 }
    if ('formaction' in attr)  { attr.formaction=  _proxy_jslib_full_url(attr.formaction, doc, reverse) ;  rebuild= 1 }
    if ('background' in attr)  { attr.background=  _proxy_jslib_full_url(attr.background, doc, reverse) ;  rebuild= 1 }
    if ('usemap' in attr)      { attr.usemap=      _proxy_jslib_full_url(attr.usemap, doc, reverse) ;      rebuild= 1 }
    if ('cite' in attr)        { attr.cite=        _proxy_jslib_full_url(attr.cite, doc, reverse) ;        rebuild= 1 }
    if ('longdesc' in attr)    { attr.longdesc=    _proxy_jslib_full_url(attr.longdesc, doc, reverse) ;    rebuild= 1 }
    if ('codebase' in attr)    { attr.codebase=    _proxy_jslib_full_url(attr.codebase, doc, reverse) ;    rebuild= 1 }
    if ('poster' in attr)      { attr.poster=      _proxy_jslib_full_url(attr.poster, doc, reverse) ;      rebuild= 1 }
    if ('pluginspage' in attr) { attr.pluginspage= _proxy_jslib_full_url(attr.pluginspage, doc, reverse) ; rebuild= 1 }

    if ((tag_name=='meta') && attr['http-equiv'] && attr['http-equiv'].match(/^\s*refresh\b/i)) {
	attr.content= _proxy_jslib_global_replace(
			  attr.content,
			  /(\;\s*URL\=)\s*(\S*)/i,
			  function (a) { return a[1] + _proxy_jslib_full_url(a[2], doc, reverse) } ) ;
	rebuild= 1 ;
    }


    // Now attr[] has been modified correctly.


    var iframe_jslib= '', iframe_id ;
    if (tag_name=='iframe' && (attr.src.match(/^about\:blank$/i) || (attr.src==''))) {
	if ((attr.id==void 0) || (attr.id=='')) {
	    iframe_id= _proxy_jslib_random_string(10) ;
	    attr.id= iframe_id ;
	    rebuild= 1 ;
	} else {
	    attr.id= attr.id.replace(/\W/g, '') ;
	    iframe_id= attr.id ;
	}
	var dummy_iframe_id= _proxy_jslib_random_string(10) ;
	iframe_jslib= "</iframe><script>"
		    + "_proxy_jslib_init_iframe(document.getElementById('" + iframe_id + "')) ;"
		    + '</script><iframe id="' + dummy_iframe_id + '">' ;
    }


    if (!rebuild) return element ;

    attrs= '' ;
//    for (name in attr) {
    for (i= 0 ; i<names.length ; i++) {
	name= names[i] ;
	if (attr[name]==null) continue ;
	if (attr[name]=='')  { attrs+= ' '+name ; continue }
	if (!attr[name].match(/\"/) || attr[name].match(/\'/)) {
	    attrs+= ' '+name+'="'+_proxy_jslib_html_escape(attr[name])+'"' ;
	} else {
	    attrs+= ' '+name+"='"+_proxy_jslib_html_escape(attr[name])+"'" ;
	}
    }

    end_slash= element.match(/\/\s*>?$/)  ? ' /'  : '' ;
    return '<'+tag_name+attrs+end_slash+'>'+iframe_jslib ;
}


function _proxy_jslib_random_string(len) {
    var chars= '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('') ;
    var ret= '' ;
    for (var i= 0 ; i<len ; i++) ret+= chars[Math.random()*chars.length] ;
    return ret ;
}



function _proxy_jslib_element2tag (e) {
    var ret= '', i ;
if (e.nodeType!=1) alert('in element2tag; nodeType=['+e.nodeType+']') ;
    for (i= 0 ; i<e.attributes.length ; i++)
	ret+= ' '+e.attributes[i].nodeName+'="'+e.attributes[i].nodeValue+'"' ;
    ret= '<'+e.tagName+ret+'>' ;
    for (i=0 ; i<e.childNodes.length ; i++)
	if      (e.childNodes[i].nodeType==1) ret+= '\n'+_proxy_jslib_element2tag(e.childNodes[i]) ;
	else if (e.childNodes[i].nodeType==3) ret+= '\n'+e.childNodes[i].nodeValue ;
    return ret ;
}



// This mimics much of _proxy_jslib_proxify_element(), above.
function _proxy_jslib_proxify_attribute(element, name, value, reverse) {
    if (/\&\{.*\}\;/.test(value)) return ;

    name= name.toLowerCase() ;

    // when proxifying URL, assume it's in a frame, since most of the time this
    //   routine is called it will be in a frame... not perfect....
    if (/^(href|src|lowsrc|dynsrc|action|background|usemap|cite|longdesc|codebase|poster)$/i.test(name)) {
	//return _proxy_jslib_full_url(value, null, reverse) ;
	return _proxy_jslib_full_url_by_frame(value, null, true, reverse) ;
    } else if (/^on/i.test(name)) {
	return _proxy_jslib_proxify_block(value, _proxy_jslib_default_script_type,
			_proxy_jslib_ALLOW_UNPROXIFIED_SCRIPTS, reverse) ;
    } else if (/^style$/i.test(name)) {
	if (/(expression|function)\s*\(/i.test(value)) return ;
	else return value ;
    } else if (/^data$/i.test(name) && element.nodeName.match(/^object$/i)) {
	return _proxy_jslib_full_url_by_frame(value, null, true, reverse) ;
    } else {
	return value ;
    }
}



function _proxy_jslib_proxify_block(s, type, unknown_type_ok, reverse) {
    if (type) type= type.toLowerCase() ;

    if (type=='text/css') {
	return _proxy_jslib_proxify_css(s, reverse) ;

    } else if (type && type.match(/^(application\/x\-javascript|application\/x\-ecmascript|application\/javascript|application\/ecmascript|text\/javascript|text\/ecmascript|text\/livescript|text\/jscript)$/)) {
	return _proxy_jslib_proxify_js(s, 1, void 0, void 0, reverse) ;

    } else {
	return unknown_type_ok ? s : '' ;
    }
}



function _proxy_jslib_proxify_css(css, reverse) {
    // false in, false out
   if (!css) return css ;

    var out= '', m1 ;
    while (m1= css.match(/\burl\s*\(\s*(([^\)]*\\\))*[^\)]*)(\)|$)/i)) {
	out+= css.substr(0,m1.index) + 'url(' + _proxy_jslib_css_full_url(m1[1], null, reverse) + ')' ;
	css= css.substr(m1.index+m1[0].length) ;
    }
    out+= css ;

    css= out ;
    out= '' ;
    while (m1=css.match(/\@import\s*(\"[^"]*\"|\'[^']*\'|[^\;\s\<]*)/i)) {
	if (!m1[1].match(/^url\s*\(/i)) {   // to avoid use of "(?!...)"
	    out+= css.substr(0,m1.index) + '@import ' + _proxy_jslib_css_full_url(m1[1], null, reverse) ;
	} else {
	    out+= css.substr(0,m1.index) + m1[0] ;
	}
	css= css.substr(m1.index+m1[0].length) ;
    }
    out+= css ;

    css= out ;
    out= '' ;
    while (m1= css.match(/((expression|function)\s*\()([^)]*)/i)) {
	out+= css.substr(0,m1.index) + m1[1] + _proxy_jslib_proxify_js(m1[3], void 0, void 0, void 0, reverse) ;
	css= css.substr(m1.index+m1[0].length) ;
    }
    out+= css ;

    return out ;
}


function _proxy_jslib_css_full_url(url, doc, reverse) {
    var q= '' ;
    url= url.replace(/\s+$/, '') ;
    if      (url.match(/^\"/)) { q= '"' ; url= url.replace(/^\"|\"$/g, '') }
    else if (url.match(/^\'/)) { q= "'" ; url= url.replace(/^\'|\'$/g, '') }
    url= url.replace(/\\(.)/g, "$1").replace(/^\s+|\s+$/g, '') ;
    url= _proxy_jslib_full_url(url, doc, reverse) ;
    url= url.replace(/([\(\)\,\s\'\"\\])/g, function (p) { return '\\'+p } ) ;
    return q+url+q ;
}



function _proxy_jslib_return_frame_doc(enc_URL, doc) {
    var top_URL= _proxy_jslib_html_escape(_proxy_jslib_url_start_inframe
					  + _proxy_jslib_wrap_proxy_encode('x-proxy://frames/topframe?URL='
								      + encodeURIComponent(enc_URL) ) ) ;
    var page_URL= _proxy_jslib_html_escape(_proxy_jslib_url_start_inframe + enc_URL) ;
    doc.open();
    doc.write('<html>\n<frameset rows="80,*">\n'
	    + '<frame src="'+top_URL+'">\n<frame src="'+page_URL+'" name="_proxy_jslib_main_frame">\n'
	    + '<\/frameset>\n</html>') ;
    doc.close() ;
//alert('in return_frame_doc, after writing doc; top_URL, page_URL=\n['+top_URL+']\n['+page_URL+']') ;
}



//---- everything needed to handle proxify_js() ------------------------

// This takes a string as input, and returns a string as output.  It calls
//   _proxy_jslib_proxify_js_tokens() to do the real work.
// Currently this only returns the proxified string, not the remainder.
// It turns out that Array.shift() and Array.unshift() are implemented
//   inefficiently in both Firefox and MSIE, such that it seems to require
//   the whole Array to shift down in memory; thus, shifting the whole array
//   goes as O(n^2).  Additionally, Array.pop() is implemented equally
//   inefficiently in MSIE, i.e. the time for one pop() is proportional to
//   the length of the array.  Thus, this routine is written to maintain a
//   single unchanging token array with pointers into it, which is probably
//   a good approach anyway.
function _proxy_jslib_proxify_js(s, top_level, with_level, in_new_statement, reverse) {
    if ((s==void 0) || (s=='')) return s ;
    if (with_level==void 0) with_level= 0 ;
    if (in_new_statement==void 0) in_new_statement= 0 ;

    // ... until _proxy_jslib_proxify_js_tokens_reverse() is complete
    if (reverse) return s;

    // hack for eval()-- return unchanged if it's not a string or String object
    if (!((typeof s=='string') || (s instanceof String) || (s instanceof Array)))
	return s ;

    var jsin= _proxy_jslib_tokenize_js(s) ;

    // next routine really needs completion and more testing....
    //if (reverse) return _proxy_jslib_proxify_js_tokens_reverse(jsin, 0, jsin.length) ;

    return _proxy_jslib_proxify_js_tokens(jsin, 0, jsin.length, top_level, with_level, in_new_statement, reverse) ;
}



function _proxy_jslib_proxify_js_tokens_reverse(jsin, start, end)
{
_proxy_jslib_ORIGINAL_WINDOW_alert.call(window, 'in _proxy_jslib_proxify_js_tokens_reverse(), \nbefore: ['+jsin.slice(start, end).join('')+']') ;
    var RE= _proxy_jslib_RE ;

    var i, i_jsin, out, element, token, match, p, op, estart, eend, tstart, tend ;

    out= [] ;
    out.push= _proxy_jslib_ORIGINAL_ARRAY_push ;  // hack to use original ARRAY.push()

    i_jsin= start ;

    while (i_jsin<end) {
	element= jsin[i_jsin++] ;
	token= element.skip  ? void 0  : element ;

	if (token=='_proxy_jslib_handle') {
	    if (jsin[i_jsin+1]=='null') {
		out.push(jsin[i_jsin+7]) ;
		i_jsin+= 15 ;
	    } else {
		estart= i_jsin+1 ;
		i_jsin= eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 0) ;
		out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
		if (match= jsin[i_jsin+2].match(/^'(\w+)'$/)) {
		    out.push('.', match[1]) ;
		    i_jsin+= 13 ;
		} else if (jsin[i_jsin+2]=='(') {
		    out.push('[') ;
		    estart= i_jsin+3 ;
		    eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 1) ;
		    out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
		    out.push(']') ;
		    if (jsin[eend]!= ')')
			alert('error parsing _proxy_jslib_handle; next token is ['+jsin[eend]+']') ;
		    i_jsin= eend+11 ;
		} else {
		    alert('error parsing _proxy_jslib_handle; next token is ['+jsin[i_jsin+2]+']') ;
		    break ;
		}
	    }

	} else if (token=='_proxy_jslib_assign') {
	    if (jsin[i_jsin+1]=="''") {
		tstart= i_jsin+4 ;
		tend= _proxy_jslib_get_next_js_expr(jsin, tstart, end, 0) ;
		out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, tstart, tend)) ;
		if (match= jsin[tend+2].match(/^'(\w+)'$/)) {
		    out.push('.', match[1]) ;
		    op= jsin[tend+5].match(/^'([^']*)'$/)[1] ;
		    out.push(op) ;
		    if (jsin[tend+8]=="''") {
			i_jsin= tend+10 ;
		    } else if (jsin[tend+8]=='(') {
			estart= tend+9 ;
			eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 1) ;
			out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
			i_jsin= eend+2 ;
		    } else {
			alert('error parsing _p_j_assign; next token is ['+jsin[tend+8]+']') ;
		    }
		} else if (jsin[tend+2]=='(') {
		    out.push('[') ;
		    estart= tend+3 ;
		    eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 1) ;
		    out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
		    out.push(']') ;
		    op= jsin[eend+3].match(/^'([^']*)'$/)[1] ;
		    out.push(op) ;
		    if (jsin[eend+6]=="''") {
			i_jsin= eend+8 ;
		    } else if (jsin[eend+6]=='(') {
			estart= eend+7 ;
			eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 1) ;
			out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
			i_jsin= eend+2 ;
		    } else {
			alert('error parsing _p_j_assign; next token is ['+jsin[eend+6]+']') ;
		    }
		} else {
		    alert('error parsing _p_j_assign; next token is ['+jsin[tend+2]+']') ;
		}
	    } else if (match= jsin[i_jsin+1].match(/^'(\+\+|--|delete)'$/)) {
		op= match[1] ;
		out.push(op) ;
		tstart= i_jsin+4 ;
		tend= _proxy_jslib_get_next_js_expr(jsin, tstart, end, 0) ;
		out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, tstart, tend)) ;
		if (match= jsin[tend+2].match(/^'(\w+)'$/)) {
		    out.push('.', match[1]) ;
		    i_jsin= tend+10 ;
		} else if (jsin[tend+2]=='(') {
		    out.push('[') ;
		    estart= tend+3 ;
		    eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 1) ;
		    out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
		    out.push(']') ;
		    i_jsin= _proxy_jslib_get_next_js_expr(jsin, eend+2, end, 1) + 1 ;
		} else {
		    alert('error parsing _p_j_assign; next token is ['+jsin[tend+2]+']') ;
		}
	    } else {
		alert('error parsing _p_j_assign; next token is ['+jsin[i_jsin+1]+']') ;
	    }

	} else if (token=='_proxy_jslib_assign_rval') {
	    out.pop() ; out.pop() ;
	    p= out.pop() ;
	    if (jsin[i_jsin+1]=="''") {
		if (match= jsin[i_jsin+4].match(/^'(\w+)'$/)) {
		    if (p!=match[1])
			alert('error parsing _proxy_jslib_assign_rval; p doesn\'t match') ;
		    out.push(p) ;
		    if (match= jsin[i_jsin+7].match(/^'(\+\+|--)'$/)) {
			out.push(match[1]) ;
			i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+13, end, 1) + 1 ;
		    } else if (match= jsin[i_jsin+7].match(/^'([^']+)'$/)) {
			out.push(match[1]) ;
			if (jsin[i_jsin+10]=='(') {
			    estart= i_jsin+11 ;
			    eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 1) ;
			    out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
			    i_jsin= _proxy_jslib_get_next_js_expr(jsin, eend+2, end, 1) + 1 ;
			} else {
			    alert('error parsing _proxy_jslib_assign_rval; next token is ['+jsin[i_jsin+10]+']') ;
			}
		    } else {
			alert('error parsing _proxy_jslib_assign_rval; next token is ['+jsin[i_jsin+7]+']') ;
		    }
		} else {
		    alert('error parsing _proxy_jslib_assign_rval; missing prop') ;
		}
	    } else if (match= jsin[i_jsin+1].match(/^'(\+\+|--|delete)'$/)) {
		out.push(match[1]) ;
		if (match= jsin[i_jsin+4].match(/^'(\w+)'$/)) {
		    out.push(match[1]) ;
		    i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+13, end, 1) ;
		} else {
		    alert('error parsing _proxy_jslib_assign_rval; missing prop') ;
		}
	    } else {
		alert('error parsing _proxy_jslib_assign_rval; bad prefix') ;
	    }

	} else if (token=='_proxy_jslib_with_handle') {
	    out.push(jsin[i_jsin+7]) ;
	    jsin+= 15 ;

	} else if (token=='_proxy_jslib_with_assign_rval') {
	    out.pop() ; out.pop() ;
	    p= out.pop() ;
	    match= jsin[i_jsin+7].match(/^'(\w+)'$/) ;
	    if (p!=match[1])
		alert('error parsing _proxy_jslib_with_assign_rval; p doesn\'t match') ;
	    if (jsin[i_jsin+4]=="''") {
		out.push(p) ;
		if (match= jsin[i_jsin+10].match(/^'(\+\+|--)'$/)) {
		    out.push(match[1]) ;
		    i_jsin+= 18 ;
		} else if (match= jsin[i_jsin+10].match(/^'([^']+)'$/)) {
		    out.push(match[1]) ;
		    estart= i_jsin+14 ;
		    eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 1) ;
		    out.push(_proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend)) ;
		    i_jsin= eend+5 ;
		} else {
		    alert('error parsing _proxy_jslib_with_assign_rval; next token is ['+jsin[i_jsin+10]+']') ;
		}
	    } else if (match= jsin[i_jsin+4].match(/^'(\+\+|--|delete)'$/)) {
		out.push(match[1], p) ;
		i_jsin+= 18 ;
	    } else {
		alert('error parsing _proxy_jslib_with_assign_rval; prefix is ['+jsin[i_jsin+4]+']') ;
	    }

	} else if (token=='eval' && jsin[i_jsin]=='(') {
	    estart= i_jsin+4 ;
	    eend= _proxy_jslib_get_next_js_expr(jsin, estart, end, 0) ;
	    out.push('eval(', _proxy_jslib_proxify_js_tokens_reverse(jsin, estart, eend), ')') ;
	    i_jsin= eend+9 ;

	} else if (token=='_proxy_jslib_increments') {
	    if (jsin[i_jsin]==')') {
		out.length-= 5 ;
		i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+6, end, 1) + 1 ;
	    } else {
		i_jsin+= 5 ;
	    }

	} else if (token=='_proxy_jslib_with_objs') {
	    if (jsin[i_jsin]=='=') {
		out.pop(); out.pop(); out.pop() ;
		i_jsin+= 6 ;
	    } else if (jsin[i_jsin]=='[') {
		i_jsin+= 7 ;
	    } else if (jsin[i_jsin]=='.') {
		i_jsin+= 6 ;
	    }

	} else if (token=='_proxy_jslib_new_function') {
	    out.push('new Function') ;

	} else if (token=='_proxy_jslib_flush_write_buffers') {
	    i_jsin+= 3 ;

	} else if (match= element.match(/^_proxy(\d+)_/)) {
	    out.push(element.replace(/^_proxy\d+/, '_proxy'+(match[1]>1 ? match[1]-1 : '') )) ;
	    

	} else {
	    out.push(element) ;
	}
    }

_proxy_jslib_ORIGINAL_WINDOW_alert.call(window, 'in _proxy_jslib_proxify_js_tokens_reverse(), \nbefore: ['+jsin.slice(start, end).join('')+']\nafter: ['+out.join('')+']') ;
    return out.join('') ;
}



// This takes an array range of tokens as input, and returns a string.
// Note that the jsin array never changes; rather, we manipulate pointers
//   into it.  This includes when it is called recursively.
function _proxy_jslib_proxify_js_tokens(jsin, start, end, top_level, with_level, in_new_statement, reverse)
{
    var RE= _proxy_jslib_RE ;

    var i_jsin, i_jsin_start, out, element, token, last_token, new_last_token, newline_since_last_token,
	term_so_far= '', sub_expr, op, new_val, cur_val_str, inc_by,
	in_braces= 0, in_func= false, expr, new_expr,
	var_decl, varname, eq, value, skip1, skip2, funcname, with_obj, code,
	match, m2, o_p, ostart, oend, pstart, pend, p, estart, eend,
	skipped, i, i_next_token, i_lt, next_token, next_expr, next_expr_st, skipped, args, fn_body, t ;


    out= [] ;
    out.push= _proxy_jslib_ORIGINAL_ARRAY_push ;  // hack to use original ARRAY.push()

    if (top_level) _proxy_jslib_does_write= false ;

    i_jsin= start ;

  OUTER:
    while (i_jsin<end) {
	i_jsin_start= i_jsin;
	element= jsin[i_jsin++] ;
	token= element.skip  ? void 0  : element ;

	if (RE.LINETERMINATOR.test(element)) newline_since_last_token= true ;
	new_last_token= '' ;

	if (token=='{') {
	    in_braces++ ;
	} else if (token=='}') {
	    if (--in_braces==0) in_func= false ;
	}


	// locate next token in jsin, and whether we skip a line terminator
	i_next_token= i_lt= i_jsin ;
	while (i_next_token<end && jsin[i_next_token].skip) i_next_token++ ;
	next_token= (i_next_token<end)  ? jsin[i_next_token]  : void 0 ;
	while (i_lt<i_next_token && !RE.LINETERMINATOR.test(jsin[i_lt])) i_lt++ ;
	if (i_lt==i_next_token) i_lt= void 0 ;


	// start of the main switch block

	if (!token) {
	    if (term_so_far) term_so_far+= element ;
	    else out.push(element) ;

	} else if (match= token.match(/^\_proxy(\d*)(\_.*)/))   {
	    // the "-0" is to typecast match[1] to a number
	    term_so_far+= '_proxy'+(match[1]-0+1)+match[2] ;

	} else if (RE.N_S_RE.test(token)) {
	    out.push(term_so_far) ;
	    term_so_far= token ;

	} else if (/^(\+\+|\-\-|delete)$/.test(token)) {
	    // peek ahead to see if we're in "-->"
	    if (token=='--' && (next_token=='>')) {
		i_jsin= i_next_token+1 ;
		out.push(term_so_far, '-->') ;
		term_so_far= '' ;
	    } else if (term_so_far!='' && !newline_since_last_token) {
		out.push(term_so_far, token) ;
		term_so_far= '' ;
	    } else {
		out.push(term_so_far) ;
		term_so_far= '' ;

		var start_parens= 0;
		while (jsin[i_next_token]=='(') {
		    start_parens++;
		    i_jsin= i_next_token+1;
		    while (jsin[i_jsin].skip) i_jsin++;
		    i_next_token= i_jsin;
		}

		o_p= _proxy_jslib_get_next_js_term(jsin, i_jsin, end) ;
		if (o_p==void 0) break ;
		ostart= o_p[0] ;
		oend=   o_p[1] ;
		pstart= o_p[2] ;
		pend=   o_p[3] ;

		i_next_token= pend;
		while (jsin[i_next_token].skip) i_next_token++;
		while (start_parens) {
		    if (jsin[i_next_token]!=')') break OUTER;
		    new_last_token= ')';
		    start_parens--;
		    i_next_token++;
		    while (jsin[i_next_token].skip) i_next_token++;
		}

		if (oend>ostart+1) {
		    if (pstart>=pend) {
			p= '' ;
			out.concat(token, jsin.slice(i_jsin_start, i_next_token));
		    } else if (jsin[pstart]=='[') {
			p= _proxy_jslib_proxify_js_tokens(jsin, pstart+1, pend-1, 0, with_level) ;
			out.push(" _proxy_jslib_assign('" + token + "', ("
				+ _proxy_jslib_proxify_js_tokens(jsin, ostart, oend, 0, with_level) + "), ("
				+ p + "), '')" ) ;
		    } else {
			out.push(" _proxy_jslib_assign('" + token + "', ("
				+ _proxy_jslib_proxify_js_tokens(jsin, ostart, oend, 0, with_level)
				+ "), '"  + jsin[pstart] + "', '')" ) ;  // should be single identifier
		    }
		} else {
		    if (jsin[pstart]=='[') {
			p= _proxy_jslib_proxify_js_tokens(jsin, pstart+1, pend-1, 0, with_level) ;
			out.push(" _proxy_jslib_assign('" + token + "', ("
				+ _proxy_jslib_proxify_js_tokens(jsin, ostart, oend, 0, with_level) + "), ("
				+ p + "), '')" ) ;
		    } else {
			p= jsin[pstart] ;   // should be single identifier
			if (token=='delete')
			    out.push('delete ' + p);
			else 
			    out.push("(" + p + "= _proxy_jslib_assign_rval('"
				     + token + "', '" + p + "', '', '', "
				     + "(typeof " + p + "=='undefined' ? void 0 : " + p + ")))") ;
		    }
		}
		i_jsin= i_next_token ;
	    }


	} else if (token=='eval' && (next_token=='(')) {
	    estart= i_jsin= i_next_token+1 ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
	    if (i_jsin==void 0 || i_jsin>=end || jsin[i_jsin++]!=')') break ;

	    term_so_far+= 'eval(_proxy_jslib_proxify_js(('
			+ _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level)
			+ '), 0, ' + with_level + ') )' ;
	    _proxy_jslib_needs_jslib= true ;


	// Testing a hash of booleans here doesn't seem to be any faster than
	//   using this long regex, unfortunately.  For example:
	//      } else if (RE.SET_TRAPPED_PROPERTIES[token]) {
	} else if (/^(open|assign|write|writeln|replace|load|eval|setInterval|setTimeout|toString|String|src|currentSrc|href|background|lowsrc|action|formAction|location|poster|URL|url|newURL|oldURL|referrer|baseURI|useMap|longDesc|cite|codeBase|profile|cssText|insertRule|setStringValue|setProperty|backgroundImage|content|cursor|listStyleImage|host|hostname|pathname|port|protocol|search|setNamedItem|innerHTML|outerHTML|outerText|body|insertAdjacentHTML|setAttribute|setAttributeNode|getAttribute|nodeValue|value|cookie|domain|frames|parent|top|opener|execScript|execCommand|navigate|showModalDialog|showModelessDialog|LoadMovie|close|getElementById|getElementsByTagName|appendChild|replaceChild|insertBefore|text|textContent|origin|postMessage|pushState|replaceState)$/.test(token)) {
	    _proxy_jslib_needs_jslib= true ;
	    _proxy_jslib_does_write= _proxy_jslib_does_write || (token=='write') || (token=='writeln') || (token=='eval') ;
	    if ( newline_since_last_token
		 &&   /^(\)|\]|\+\+|\-\-)$|^([a-zA-Z\$\_\\\d'"]|\.\d|\/..)/.test(last_token)
		 && ! /^(case|delete|do|else|in|instanceof|new|typeof|void|function|var)$/.test(last_token) )
	    {
		out.push(term_so_far) ;
		term_so_far= '' ;
	    }
	    var has_dot= term_so_far.match(RE.DOTSKIPEND) ;
	    term_so_far= term_so_far.replace(RE.DOTSKIPEND, '') ;

	    var next_is_paren= (next_token=='(')  ? 1  : 0 ;

	    if (/^[\{\,]/.test(last_token) && (next_token==':')) {
		out.push(term_so_far, token) ;
		for (i= i_jsin ; i<=i_next_token ; i++) out.push(jsin[i]) ;
		i_jsin= i_next_token+1 ;

		term_so_far= '' ;
		new_last_token= ':' ;

	    } else if (token=='String' && !next_is_paren) {
		if (has_dot) term_so_far+= '.' ;
		term_so_far+= token;
		div_ok= 1;

	    } else if ((i_lt==void 0) && (next_token=='++' || next_token=='--')) {
		op= next_token ;
		i_jsin= i_next_token+1 ;
		if (term_so_far=='') {
		    out.push(' ', (with_level
				      ? (token+"= _proxy_jslib_with_assign_rval(_proxy_jslib_with_objs, '', '"+token+"', '"+op+"', '', "+token+")")
				      : (token+"= _proxy_jslib_assign_rval('', '"+token+"', '"+op+"', '', (typeof "+token+"=='undefined' ? void 0 : " + token+"))") )
			     ) ;
		} else {
		    term_so_far= " _proxy_jslib_assign('', "+term_so_far+", '"+token+"', '"+op+"', '')" ;
		}
		new_last_token= ')' ;

	    } else if (next_token && next_token.match(RE.ASSIGNOP)) {
		op= next_token ;
		estart= i_jsin= i_next_token+1 ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
		if (i_jsin==void 0) break ;
		new_val= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) ;
		if (term_so_far=='') {
		    out.push(' ', (with_level
				? (token+"= _proxy_jslib_with_assign_rval(_proxy_jslib_with_objs, '', '"+token+"', '"+op+"', ("+new_val+"), "+token+")")
				: (token+"= _proxy_jslib_assign_rval('', '"+token+"', '"+op+"', ("+new_val+"), (typeof "+token+"=='undefined' ? void 0 : " + token+"))") )
			    )
		} else {
		    term_so_far= " _proxy_jslib_assign('', "+term_so_far+", '"+token+"', '"+op+"', ("+new_val+"))" ;
		}
		new_last_token= ')' ;

	    } else {
		if (term_so_far=='') {
		    term_so_far= (with_level
				  ? (" _proxy_jslib_with_handle(_proxy_jslib_with_objs, '"+token+"', "+token+", "+next_is_paren+", "+in_new_statement+")")
				  : (" _proxy_jslib_handle(null, '"+token+"', "+token+", "+next_is_paren+", "+in_new_statement+")") ) ;
		} else {
		    term_so_far= " _proxy_jslib_handle("+term_so_far+", '"+token+"', '', "+next_is_paren+", "+in_new_statement+")" ;
		}
		new_last_token= ')' ;
	    }


	// Skip these for the JS version-- they require %IN_CUSTOM_INSERTION
	//   etc. and would be rare anyway.  Revisit later if needed.
	//} else if (/^(applets|embeds|forms|ids|layers|anchors|images|links)$/.test(token)) {

	} else if (/^(if|while|for|switch)$/.test(token)) {
	    out.push(term_so_far, token) ;
	    term_so_far= '' ;
	    if (next_token!='(') break ;
	    estart= i_jsin= i_next_token+1 ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
	    if (i_jsin==void 0 || i_jsin>=end || jsin[i_jsin++]!=')') break ;
	    out.push('(', _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level), ')') ;

	} else if (token=='catch') {
	    out.push(term_so_far, token) ;
	    term_so_far= '' ;
	    if (next_token!='(') break ;
	    estart= i_jsin= i_next_token+1 ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
	    if (i_jsin==void 0 || i_jsin>=end || jsin[i_jsin++]!=')') break ;
	    out.push('(') ;
	    for (i= estart ; i<eend ; i++) out.push(jsin[i]) ;
	    out.push(')') ;


	} else if (token=='function') {
	    out.push(term_so_far, token) ;
	    term_so_far= '' ;
	    if (next_token && next_token.match(RE.IdentifierName)) {
		for (i= i_jsin ; i<i_next_token ; i++) out.push(jsin[i]) ;
		funcname= next_token ;
		i_jsin= i_next_token+1 ;
		while (i_jsin<end-1
		       && jsin[i_jsin]=='.' && jsin[i_jsin+1].match(RE.IdentifierName)) {
		    funcname+= jsin[i_jsin] + jsin[i_jsin+1] ;
		    i_jsin+= 2 ;
		}
	    } else {
		funcname= '' ;
	    }
	    if (m2= funcname.match(/^_proxy(\d*)_/))
		funcname= '_proxy' + (m2[1]-0+1) + funcname.replace(/^_proxy(\d*)/, '') ;
	    out.push(funcname) ;
	    i_next_token= i_jsin ;
	    while (i_next_token<end && jsin[i_next_token].skip) i_next_token++ ;
	    for (i= i_jsin+1 ; i<i_next_token ; i++) out.push(jsin[i]) ;
	    if (jsin[i_next_token]!='(') break ;
	    estart= i_jsin= i_next_token+1 ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
	    if (i_jsin==void 0 || i_jsin>=end || jsin[i_jsin++]!=')') break ;
	    out.push('(') ;
	    for (i= estart ; i<eend ; i++) out.push(jsin[i]) ;
	    out.push(') {') ;
	    while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
	    if (i_jsin>=end || jsin[i_jsin++]!='{') break ;

	    in_braces++ ;
	    in_func= true ;


	} else if (token=='with') {
	    out.push(term_so_far) ;
	    term_so_far= '' ;
	    skip1= '' ;
	    for (i= i_jsin ; i<i_next_token ; i++) skip1+= jsin[i] ;
	    if (next_token!='(') break ;
	    estart= i_jsin= i_next_token+1 ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
	    with_obj= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) ;
	    if (i_jsin>=end || jsin[i_jsin++]!=')') break ;
	    skip2= '' ;
	    while (i_jsin<end && jsin[i_jsin].skip) skip2+= jsin[i_jsin++] ;
	    if (jsin[i_jsin]=='{') {
		estart= ++i_jsin ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
		code= '{' + _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level+1) + '}' ;
		if (i_jsin>=end || jsin[i_jsin++]!='}') break ;
	    } else {
		estart= i_jsin ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
		code= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level+1) ;
		while (jsin[i_jsin]==',') {
		    estart= ++i_jsin ;
		    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
		    code+= ',' + _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level+1) ;
		}
	    }
	    out.push('{', with_level  ? ''  : 'var _proxy_jslib_with_objs= [] ;') ;
	    out.push('with', skip1, '(_proxy_jslib_with_objs[_proxy_jslib_with_objs.length]= (', with_obj, '))', skip2, code) ;
	    out.push('; _proxy_jslib_with_objs.length-- ;}') ;
	    new_last_token= ';' ;


	} else if (token=='var' || token=='let') {
	    out.push(term_so_far, token) ;
	    term_so_far= '' ;
	    while (1) {
		estart= i_jsin ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
		i= estart ;
		while (i<eend && jsin[i].skip) out.push(jsin[i++]) ;
		varname= (i<eend)  ? jsin[i]  : void 0 ;
		if (!varname || !varname.match(RE.IdentifierName)) break OUTER ;
		if (varname && (match= varname.match(/^_proxy(\d*)_/)))
		    varname= '_proxy' + (match[1]-0+1) + varname.replace(/^_proxy(\d*)/, '') ;
		out.push(varname) ;
		i++ ;
		while (i<eend && jsin[i].skip) out.push(jsin[i++]) ;
		eq= (i<eend)  ? jsin[i]  : void 0 ;
		if (eq && !(eq=='=' || eq=='in')) break OUTER ;

		if (eq) out.push(eq, _proxy_jslib_proxify_js_tokens(jsin, i+1, eend, 0, with_level)) ;
		if (i_jsin>=end || jsin[i_jsin]!=',') break ;
		i_jsin++ ;
		out.push(',') ;
	    }


	} else if (token=='new') {
	    out.push(term_so_far) ;
	    term_so_far= '' ;

	    // jsm-- must also handle "new window.Function", "new (window.Function)", etc.
	    if (next_token=='Function') {
		i_jsin= i_next_token+1 ;
		out.push('_proxy_jslib_new_function') ;

	    } else if (next_token=='function') {
		term_so_far= 'new function' ;
		i_jsin= i_next_token+1 ;
		while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
		if (i_jsin>=end || jsin[i_jsin++]!='(') break ;
		estart= i_jsin ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
		if (i_jsin>=end || jsin[i_jsin++]!=')') break ;
		term_so_far+= '(' ;
		for (i= estart ; i<eend ; i++) term_so_far+= jsin[i] ;
		term_so_far+= ')' ;
		while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
		if (i_jsin>=end || jsin[i_jsin++]!='{') break ;
		estart= i_jsin ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
		if (i_jsin>=end || jsin[i_jsin++]!='}') break ;
		fn_body= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level, 0) ;
		term_so_far+= '{'+fn_body+'}' ;
		new_last_token= '}' ;

	    } else if ((next_token=='Audio') || (next_token=='EventSource') || (next_token=='WebSocket') || (next_token=='Worker')) {
		i_jsin= i_next_token+1 ;
		while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
		if (jsin[i_jsin]=='(') {
		    estart= ++i_jsin ;
		    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
		    var arg1= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level, 0) ;
		    estart= i_jsin ;
		    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
		    var other_args= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level, 0) ;
		    if (i_jsin>=end || jsin[i_jsin++]!=')') break ;
		    if (arg1!='') {
			term_so_far= 'new '+next_token+'(_proxy_jslib_full_url('+arg1+') '+other_args+')' ;
		    } else {
			term_so_far= 'new '+next_token+'()' ;
		    }
		} else {
		    term_so_far= 'new '+next_token+'()' ;
		}
		new_last_token= ')' ;


	    } else {
		if (next_token=='(') {
		    estart= i_jsin= i_next_token+1 ;
		    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
		    if (i_jsin>=end || jsin[i_jsin++]!=')') break ;
		} else {
		    estart= i_jsin ;
		    eend= i_jsin= _proxy_jslib_get_next_js_constructor(jsin, i_jsin, end) ;
		}
		new_expr= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level, 1) ;
		term_so_far+= 'new ('+new_expr+')' ;
		new_last_token= ')' ;
	    }


	} else if ((token=='return') && !in_func && top_level) {
	    out.push(term_so_far) ;
	    term_so_far= '' ;
	    _proxy_jslib_needs_jslib= true ;
	    estart= i_jsin= i_next_token ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
	    while (jsin[i_jsin]==',') {
		estart= ++i_jsin ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
	    }
	    new_expr= estart==eend  ? 'void 0'  : _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) ;
	    out.push('return ((_proxy_jslib_ret= (', new_expr, ')), _proxy_jslib_flush_write_buffers(), _proxy_jslib_ret)') ;


	} else if (/^(abstract|boolean|break|byte|case|char|class|const|continue|debugger|default|delete|do|else|enum|export|extends|final|finally|float|goto|implements|in|instanceof|int|interface|long|native|package|private|protected|return|short|static|synchronized|throw|throws|transient|try|typeof|void|volatile)$/.test(token)) {
	    out.push(term_so_far, token) ;
	    term_so_far= '' ;

	} else if (token.match(RE.IDENTIFIER)) {
	    if ( newline_since_last_token
		 &&   /^(\)|\]|\+\+|\-\-)$|^([a-zA-Z\$\_\\\d'"]|\.\d|\/..)/.test(last_token)
		 && ! /^(case|delete|do|else|in|instanceof|new|typeof|void|function|var)$/.test(last_token) )
	    {
		out.push(term_so_far) ;
		term_so_far= token ;
	    } else {
		term_so_far+= token ;
	    }

	} else if (token=='.') {
	    term_so_far+= '.' ;

	} else if (token=='(') {
	    _proxy_jslib_does_write= true ;
	    estart= i_jsin ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
	    if (i_jsin>=end || jsin[i_jsin++]!=')') break ;
	    term_so_far+= '(' + _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) + ')' ;
	    new_last_token= ')' ;


	} else if (token=='[') {
	    estart= i_jsin ;
	    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
	    if (i_jsin>=end || jsin[i_jsin++]!=']') break ;
	    if (eend-estart<=1 && ! /\D/.test(jsin[estart])) {
		term_so_far+= '['+(eend!=estart ?jsin[estart] :'')+']' ;
		new_last_token= ']' ;


	    } else {
		sub_expr= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) ;
		if (term_so_far) {
		    _proxy_jslib_needs_jslib= true ;
		    new_last_token= ')' ;

		    // locate next token in jsin, and whether we skip a line terminator
		    i_next_token= i_lt= i_jsin ;
		    while (i_next_token<end && jsin[i_next_token].skip) i_next_token++ ;
		    next_token= (i_next_token<end)  ? jsin[i_next_token]  : void 0 ;
		    while (i_lt<i_next_token && !RE.LINETERMINATOR.test(jsin[i_lt])) i_lt++ ;
		    if (i_lt==i_next_token) i_lt= void 0 ;

		    var next_is_paren= (jsin[i_next_token]=='(')  ? 1  : 0 ;

		    if ((i_lt==void 0) && (next_token=='++' || next_token=='--')) {
			op= next_token ;
			i_jsin= i_next_token+1 ;
			term_so_far= " _proxy_jslib_assign('', "+term_so_far+", ("+sub_expr+"), '"+op+"', '')" ;
		    } else if (next_token && next_token.match(RE.ASSIGNOP)) {
			op= next_token ;
			estart= i_jsin= i_next_token+1 ;
			eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 0) ;
			new_val= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) ;
			term_so_far= " _proxy_jslib_assign('', "+term_so_far+", ("+sub_expr+"), '"+op+"', ("+new_val+"))" ;
		    } else {
			term_so_far= " _proxy_jslib_handle("+term_so_far+", ("+sub_expr+"), '', "+next_is_paren+", "+in_new_statement+")" ;
		    }
		} else {
		    term_so_far= '['+sub_expr+']' ;
		    new_last_token= ']' ;
		}
	    }


	} else if (token=='{' && term_so_far=='' && last_token!=')'
		   && ((last_token==void 0) || last_token.match(RE.PUNCDIVPUNC)
		       || last_token.match(/^(?:case|delete|in|instanceof|new|return|throw|typeof)$/))
		   && (next_token.match(RE.IDENTIFIER) || next_token.match(RE.STRINGLITERAL) || next_token.match(RE.NUMERICLITERAL) || (next_token=='}') ) ) {
	    term_so_far= '{' ;
	    if (next_token!='}') {
		i_jsin= i_next_token+1 ;
		while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
		if (jsin[i_jsin]==':') {
		    term_so_far+= next_token + ':' ;
		    estart= i_jsin+1 ;
		    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, estart, end, 0) ;
		    term_so_far+= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) ;
		    while (jsin[i_jsin]==',') {
			i_jsin++ ;
			term_so_far+= ',' ;
			while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
			if (jsin[i_jsin]=='}') break ;
			if (!(jsin[i_jsin].match(RE.IDENTIFIER) || jsin[i_jsin].match(RE.STRINGLITERAL) || jsin[i_jsin].match(RE.NUMERICLITERAL)))
			    break OUTER ;
			term_so_far+= jsin[i_jsin++] ;
			while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
			if (jsin[i_jsin++]!=':')  break OUTER ;
			term_so_far+= ':' ;
			estart= i_jsin ;
			eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, estart, end, 0) ;
			term_so_far+= _proxy_jslib_proxify_js_tokens(jsin, estart, eend, 0, with_level) ;
		    }
		    if (jsin[i_jsin++]!='}') break OUTER;
		    term_so_far+= new_last_token= '}' ;

		} else {
		    out.push(term_so_far, next_token) ;
		    term_so_far= '' ;
		}

	    } else {
		i_jsin= i_next_token+1 ;
		term_so_far+= new_last_token= '}' ;
	    }



	} else if (RE.PUNCDIVPUNC.test(token)) {
	    out.push(term_so_far, token) ;
	    term_so_far= '' ;

	} else {
	    // shouldn't get here
	}

	if (token) {
	    last_token= new_last_token  ? new_last_token  : token ;
	    newline_since_last_token= false ;
	}

    }

    out.push(term_so_far) ;

    if (top_level && _proxy_jslib_does_write) {
	out.push(' ;\n_proxy_jslib_flush_write_buffers() ;') ;
	_proxy_jslib_needs_jslib= true ;
    }


    return out.join('') ;



    // This takes a token array segment as input, and returns the start and
    //   end index of the object and final property of the next JS term.  The
    //   property includes "[]" if that's what it's surrounded with.
    function _proxy_jslib_get_next_js_term(jsin, start, end) {
	var oend, pstart, pend ;
	var i_jsin= start ;

	while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
	if (i_jsin>=end || (   !jsin[i_jsin].match(RE.IDENTIFIER)
			    && !jsin[i_jsin].match(/^[\[\{\(]$/)   ) )
	    return void 0 ;
	if (jsin[i_jsin]=='[') {
	    i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+1, end, 1) ;
	    if (jsin[i_jsin]!=']') return void 0 ;
	    oend= pstart= pend= ++i_jsin ;
	} else if (jsin[i_jsin]=='{') {
	    i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+1, end, 1) ;
	    if (jsin[i_jsin]!='}') return void 0 ;
	    oend= pstart= pend= ++i_jsin ;
	} else if (jsin[i_jsin]=='(') {
	    i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+1, end, 1) ;
	    if (jsin[i_jsin]!=')') return void 0 ;
	    oend= pstart= pend= ++i_jsin ;
	} else {
	    oend= pstart= i_jsin ;
	    pend= ++i_jsin ;
	}

	while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
	while (i_jsin<end && (jsin[i_jsin]=='.' || jsin[i_jsin]=='(' || jsin[i_jsin]=='[')) {

	    if (jsin[i_jsin]=='.') {
		oend= i_jsin++ ;
		while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
		if (i_jsin>=end || !jsin[i_jsin].match(RE.IDENTIFIER)) return void 0 ;
		pstart= i_jsin++ ;
		pend= i_jsin ;

	    } else if (jsin[i_jsin]=='[') {
		oend= pstart= i_jsin ;
		i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+1, end, 1) ;
		if (i_jsin==void 0 || i_jsin>=end || jsin[i_jsin++]!=']') return void 0 ;
		pend= i_jsin ;

	    } else if (jsin[i_jsin]=='(') {
		i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin+1, end, 1) ;
		if (i_jsin==void 0 || i_jsin>=end || jsin[i_jsin++]!=')') return void 0 ;
		oend= pstart= pend= i_jsin ;
	    }
	    while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
	}
	return [start, oend, pstart, pend] ;
    }



    // Similar to _proxy_jslib_get_next_js_term(), but for "new" statements.
    function _proxy_jslib_get_next_js_constructor(jsin, start, end) {
	var c= [], t, skip= [], op, estart, eend ;
	var i_jsin= start ;

	while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
	if (i_jsin>=end || !jsin[i_jsin].match(RE.IDENTIFIER)) return void 0 ;
	i_jsin++ ;

	while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
	while (i_jsin<end && (jsin[i_jsin]=='.' || jsin[i_jsin]=='[')) {
	    if (jsin[i_jsin]=='.') {
		i_jsin++ ;
		while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
		if (i_jsin>=end || !jsin[i_jsin].match(RE.IDENTIFIER)) return void 0 ;
		i_jsin++ ;
	    } else if (jsin[i_jsin]=='[') {
		estart= ++i_jsin ;
		eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, end, 1) ;
		if (i_jsin==void 0 || i_jsin>=end || jsin[i_jsin++]!=']') return void 0 ;
	    }
	    while (i_jsin<end && jsin[i_jsin].skip) i_jsin++ ;
	}
	return i_jsin ;
    }

}


// This takes a token array segment as input, and returns an index
//   to the token following the end of the next expression in the input.
// We can't nest this because it's called from outside _proxy_jslib_proxify_js() .
function _proxy_jslib_get_next_js_expr(jsin, start, end, allow_multiple, is_new) {
    var p= [], element, last_token, i, expr_block_state ;

    var i_jsin= start ;
    while (i_jsin<end) {
	element= jsin[i_jsin] ;

	if (!allow_multiple && p.length==0 && element=='function') expr_block_state= 1 ;

	switch(element) {

	    case ';':
	    case ',':
		if (!allow_multiple && p.length==0) return i_jsin ;
		break ;

	    case '\x0a':
	    case '\x0d':
		if (!allow_multiple && p.length==0) {
		    i= i_jsin+1 ;
		    while (i<end && jsin[i].skip) i++ ;
		    if (     /^(\)|\]|\+\+|\-\-)$|^([a-zA-Z\$\_\\\d'"]|\.\d|\/..)/.test(last_token)
			&& ! /^(case|delete|do|else|in|instanceof|new|typeof|void|function|var)$/.test(last_token)
			&&   _proxy_jslib_RE.IDENTIFIER.test(jsin[i]) )
		    {
			return i_jsin ;
		    }
		    if (expr_block_state==3
			&& (jsin[i]=='{'
			    || !(jsin[i].match(_proxy_jslib_RE.PUNCDIVPUNC) || jsin[i]=='instanceof') ) )
		    {
			return i_jsin ;
		    }
		}
		break ;

	    case '{':
		i= i_jsin+1 ;
		while (i<end && jsin[i].skip) i++ ;
		if (!allow_multiple && p.length==0
		    && (expr_block_state==1 
			|| jsin[i].match(_proxy_jslib_RE.IDENTIFIER)
			|| jsin[i].match(_proxy_jslib_RE.STRINGLITERAL)
			|| jsin[i].match(_proxy_jslib_RE.NUMERICLITERAL)
			|| jsin[i]=='}' ) )
		{
		    expr_block_state= 2 ;
		}
	    case '(':
	    case '[':
	    case '?':
		if (is_new && (p.length==0) && element=='(') return i_jsin ;
		p.push(element) ;
		break ;

	    case ')':
	    case ']':
	    case '}':
	    case ':':
		if (p.length==0) return i_jsin ;
		if (p.length>0 && !(element==':' && p[p.length-1]!='?')) p.length-- ;
		//if (element=='}' && p.length==0 && !allow_multiple) return i_jsin+1 ;
		if (!allow_multiple && p.length==0 && element=='}' && expr_block_state==2)
		    expr_block_state= 3 ;
		break ;
	}

	if (!element.skip) {
	    last_token= element ;
	}

	i_jsin++ ;
    }

    return p.length==0  ? i_jsin  : void 0 ;
}



// This takes a string as input, and returns two strings as output.
function _proxy_jslib_separate_last_js_statement(s) {
    var rest, last, jsin, i, i_jsin, estart, eend, rest_end= 0 ;
    var RE= _proxy_jslib_RE ;

    jsin= _proxy_jslib_tokenize_js(s) ;

    estart= i_jsin= 0 ;
    eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, jsin.length, 0) ;
    while (eend>estart || eend<jsin.length) {
	while (i_jsin<jsin.length && jsin[i_jsin].skip) i_jsin++ ;

	// peek ahead to see if we got the last statement in jsin
	i= i_jsin ;
	while (i<jsin.length && (jsin[i]==';' || jsin[i].skip)) i++ ;
	if (i==jsin.length) break ;

	if ((jsin[i_jsin]).match(RE.STATEMENTTERMINATOR)) {
	    rest_end= ++i_jsin ;
	} else {
	    if (jsin[i_jsin]==',') i_jsin++ ;
	}

	estart= i_jsin ;
	eend= i_jsin= _proxy_jslib_get_next_js_expr(jsin, i_jsin, jsin.length, 0) ;
    }

    rest= jsin.slice(0, rest_end).join('') ;
    last= jsin.slice(rest_end, jsin.length).join('') ;
    return [rest, last] ;
}



// This takes a string as input, and returns a token array as output.
// If not for the "/" problem and the lack of \G in JavaScript, this whole
//   thing could be done in one blazing statement, if the regex below was
//   global and started with "\G":
//       out= s.match(_proxy_jslib_RE.InputElementG) ;
function _proxy_jslib_tokenize_js(s) {
    var out= [], match, element, token, div_ok, last_lastIndex= 0, conditional_state, conditional_stack_size, p_count ;
    var RE_InputElementDivG= _proxy_jslib_RE.InputElementDivG ;
    var RE_InputElementRegExpG= _proxy_jslib_RE.InputElementRegExpG ;

    while (1) {
	if (div_ok) {
	    if (!(match= RE_InputElementDivG.exec(s))) break ;
	    if (match.index!= last_lastIndex) break ;
	    last_lastIndex= RE_InputElementRegExpG.lastIndex= RE_InputElementDivG.lastIndex ;
	} else {
	    if (!(match= RE_InputElementRegExpG.exec(s))) break ;
	    if (match.index!= last_lastIndex) break ;
	    last_lastIndex= RE_InputElementDivG.lastIndex= RE_InputElementRegExpG.lastIndex ;
	}
	element= match[0] ;
	token= match[1] ;

	// if it's not a token, flag it as skippable
	if (!token) {
	    element= new String(element) ;
	    element.skip= true ;


	// pain setting div_ok to false after "if ()", etc.
	// without that requirement, half of this routine would go away.
	} else if ((token=='if') || (token=='while') || (token=='for') || (token=='switch')) {
	    conditional_state= 1 ;
	    conditional_stack_size= p_count ;

	} else if (token=='(') {
	    p_count++ ;
	    if (conditional_state==1) conditional_state= 2 ;

	} else if (token==')') {
	    p_count-- ;
	    if ((conditional_state==2) && (p_count==conditional_stack_size))
		conditional_state= 3 ;
	}


	out.push(element) ;

	if (token) {
	    if (conditional_state==3) {
		div_ok= 0 ;
		conditional_state= 0 ;
	    } else {
		div_ok= /^(\)|\]|\+\+|\-\-)$|^([a-zA-Z\$\_\\\d'"]|\.\d|\/..)/.test(token)
		    && !/^(case|delete|do|else|in|instanceof|new|return|throw|typeof|void)$/.test(token) ;
	    }
	}
    }

    RE_InputElementDivG.lastIndex= RE_InputElementRegExpG.lastIndex= 0 ;
    return out ;
}



function _proxy_jslib_set_RE() {
    if (!_proxy_jslib_RE) {  // saves time for multiple calls
	var RE= {} ;

	// count embedded parentheses carefully when using all these in matches!
	RE.WhiteSpace= '[\\x09\\x0b\\x0c \\xa0]' ;
	RE.LineTerminator= '[\\x0a\\x0d]' ;

	// messy without non-greedy matching
	//RE.Comment= '\\/\\*\\/*([^\\*]\\/|[^\\*\\/]*|\\**[^\\/])*\\*\\/|\\/\\/[^\\x0a\\x0d]*|\\<\\!\\-\\-[^\\x0a\\x0d]*' ;
	RE.Comment= '\\/\\*[\\s\\S]*?\\*\\/|\\/\\/[^\\x0a\\x0d]*|\\<\\!\\-\\-[^\\x0a\\x0d]*' ;

	RE.IdentifierStart= '[a-zA-Z\\$\\_]|\\\\u[\\da-fA-F]{4}' ;
	RE.IdentifierPart= RE.IdentifierStart+'|\\d' ;
	RE.IdentifierName= '(?:'+RE.IdentifierStart+')(?:'+RE.IdentifierPart+')*' ;

	RE.Punctuator= '\\>\\>\\>\\=?|\\=\\=\\=|\\!\\=\\=|\\<\\<\\=|\\>\\>\\=|[\\<\\>\\=\\!\\+\\*\\%\\&\\|\\^\\-]\\=|\\+\\+|\\-\\-|\\<\\<|\\>\\>|\\&\\&|\\|\\||[\\{\\}\\(\\)\\[\\]\\.\\;\\,\\<\\>\\+\\*\\%\\&\\|\\^\\!\\~\\?\\:\\=\\-]' ;
	RE.DivPunctuator= '\\/\\=?' ;

	RE.NumericLiteral= '0[xX][\\da-fA-F]+|(?:0|[1-9]\\d*)(?:\\.\\d*)?(?:[eE][\\+\\-]?\\d+)?|\\.\\d+(?:[eE][\\+\\-]?\\d+)?' ;
	RE.EscapeSequence= 'x[\\da-fA-F]{2}|u[\\da-fA-F]{4}|0|[0-3]?[0-7]\\D|[4-7][0-7]|[0-3][0-7][0-7]|[^\\dxu]' ;
	RE.StringLiteral= '"(?:[^\\"\\\\\\x0a\\x0d]|\\\\(?:'+RE.EscapeSequence+'))*"|'
			+ "'(?:[^\\'\\\\\\x0a\\x0d]|\\\\(?:"+RE.EscapeSequence+"))*'" ;
	RE.RegularExpressionLiteral= '\\/(?:[^\\x0a\\x0d\\*\\\\\\/\\[]|\\[(?:[^\\\\\\]\\x0a\\x0d]|\\\\[^\\x0a\\x0d])*\\]|\\\\[^\\x0a\\x0d])(?:[^\\x0a\\x0d\\\\\\/\\[]|\\[(?:[^\\\\\\]\\x0a\\x0d]|\\\\[^\\x0a\\x0d])*\\]|\\\\[^\\x0a\\x0d])*\\/(?:'+RE.IdentifierPart+')*' ;

	RE.Token= RE.IdentifierName+'|'+RE.NumericLiteral+'|'+RE.Punctuator+'|'+RE.StringLiteral ;

	RE.InputElementDivG= RE.WhiteSpace+'+|'+RE.LineTerminator+'|'+RE.Comment+
			    '|('+RE.Token+'|'+RE.DivPunctuator+'|'+RE.RegularExpressionLiteral+')' ;
	RE.InputElementRegExpG= RE.WhiteSpace+'+|'+RE.LineTerminator+'|'+RE.Comment+
			       '|('+RE.Token+'|'+RE.RegularExpressionLiteral+'|'+RE.DivPunctuator+')' ;

	RE.SKIP= RE.WhiteSpace+'+|'+RE.LineTerminator+'|'+RE.Comment ;
	RE.SKIP_NO_LT= RE.WhiteSpace+'+|'+RE.Comment ;

	// make RegExp objects out of the ones we'll use
	RE.InputElementDivG= new RegExp(RE.InputElementDivG, 'g') ;
	RE.InputElementRegExpG= new RegExp(RE.InputElementRegExpG, 'g') ;

	RE.LINETERMINATOR= new RegExp('^'+RE.LineTerminator+'$') ;
	RE.N_S_RE= new RegExp('^(?:'+RE.NumericLiteral+'|'+RE.StringLiteral+'|'+RE.RegularExpressionLiteral+')$') ;
	RE.DOTSKIPEND= new RegExp('\\.('+RE.WhiteSpace+'+|'+RE.LineTerminator+')*$') ;
	RE.ASSIGNOP= new RegExp('^(\\>\\>\\>\\=|\\<\\<\\=|\\>\\>\\=|[\\+\\*\\/\\%\\&\\|\\^\\-]?\\=)$') ;
	RE.NEXTISINCDEC= new RegExp('^('+RE.SKIP_NO_LT+')*(\\+\\+|\\-\\-)') ;
	RE.SKIPTOPAREN= new RegExp('^(('+RE.SKIP+')*\\()') ;
	RE.SKIPTOCOLON= new RegExp('^(('+RE.SKIP+')*\\:)') ;
	RE.SKIPTOCOMMASKIP= new RegExp('^(('+RE.SKIP+')*\\,('+RE.SKIP+')*)') ;
	RE.PUNCDIVPUNC= new RegExp('^('+RE.Punctuator+'|'+RE.DivPunctuator+')$') ;
	RE.IDENTIFIER= new RegExp('^'+RE.IdentifierName+'$') ;
	RE.STRINGLITERAL= new RegExp('^'+RE.StringLiteral+'$') ;
	RE.NUMERICLITERAL= new RegExp('^(?:'+RE.NumericLiteral+')$') ;
	RE.SKIPTOOFRAG= new RegExp('^('+RE.SKIP+')*([\\.\\[\\(])') ;
	RE.STATEMENTTERMINATOR= new RegExp('^(;|'+RE.LineTerminator+')') ;


	_proxy_jslib_RE= RE ;
    }
}



//---- utilities -------------------------------------------------------



// A replacement for instanceof, since instanceof doesn't always work in all browsers.
// Use instanceof when possible; otherwise, take a heuristic guess at the type
//   based on existing properties of the object.
// Properties are carefully selected to test correctly in both Mozilla and MSIE;
//   objects and properties vary slightly by browser.
// Unfortunately, Mozilla can't use instanceof with Link, Layer, or Form objects,
//   so the catch block will usually be called for that reason when using Mozilla.
// Note that Mozilla has a bug such that it dies when HTMLAreaElement.pathname
//   is accessed.  Thus, we avoid checking for the pathname property.
function _proxy_jslib_instanceof(o, classname) {
    if ((o==null) || ((typeof(o)!='object') && (typeof(o)!='function')))
	return false ;
    try {
	switch(classname) {
	    case 'Document':
		return ("elementFromPoint" in o) && ("createElement" in o) && ("getElementById" in o) ;
	    case 'MessageEvent':
		return ("stopImmediatePropagation" in o) && ("origin" in o) && ("ports" in o) ;
	    default:
		if (!eval(classname)) return false ;
		return eval('o instanceof ' + classname) ;
	}
    } catch(e) {

	// These are all the classes that have trouble with instanceof for some reason.
	switch(classname) {
	    case 'Window':
		return ("navigator" in o) && ("clearInterval" in o) && ("moveBy" in o) && (o.self===o.window) ;
	    case 'Link':
		return ("protocol" in o) && ("target" in o) && ("blur" in o) ;
	    case 'Location':
		return ("reload" in o) && ("protocol" in o)  && ("search" in o) ;
	    case 'Layer':
		return ("background" in o) && ("parentLayer" in o) && ("moveAbove" in o) ;
	    case 'Form':
		return ("action" in o) && ("encoding" in o) && ("submit" in o) ;
	    case 'CSS2Properties':
		return ("azimuth" in o) && ("backgroundAttachment" in o) && ("pageBreakInside" in o) ;
	    case 'CSSPrimitiveValue':
		return ("primitiveType" in o) && ("getRectValue" in o) && ("getCounterValue" in o) ;
	    case 'CSSStyleDeclaration':
		return ("getPropertyCSSValue" in o) && ("getPropertyPriority" in o) && ("removeProperty" in o) ;
	    case 'FlashPlayer':
		return ("GotoFrame" in o) && ("LoadMovie" in o) && ("SetZoomRect" in o) ;
	    case 'NamedNodeMap':
		return ("getNamedItem" in o) && ("removeNamedItem" in o) && ("setNamedItem" in o) ;
	    case 'Range':
		return ("cloneRange" in o) && ("compareBoundaryPoints" in o) && ("surroundContents" in o) ;
	    case 'Attr':
		return ("ownerElement" in o) && ("specified" in o) ;
	    case 'History':
		return ("pushState" in o) && ("replaceState" in o) && ("forward" in o) ;
	    case 'EventSource':
		// EventSource only has two properties, and they are also in WebSocket.  So
		//   test those two, and verify o is not a WebSocket.
		return ("readyState" in o) && ("url" in o) && !("bufferedAmount" in o) ;
	    case 'HashChangeEvent':
		return ("oldURL" in o) && ("newURL" in o) ;
	    case 'HTMLElement':
		return ("insertAdjacentHTML" in o) && ("outerHTML" in o) ;
	    case 'Element':
		return ("childElementCount" in o) && ("firstElementChild" in o) && ("nextElementSibling" in o) ;
	    case 'Node':
		return ("nodeName" in o) && ("nodeType" in o) && ("nodeValue" in o) ;
	    default:
		alert('error in _proxy_jslib_instanceof(): classname=[' + classname + ']; error=[' + e + ']') ;
	}
    }
}



// Using JS (not RFC) terminology, this returns:
//   full_match, protocol (with colon), authentication, host, hostname, port, pathname, search, hash
function _proxy_jslib_parse_url(in_URL) {
    var u ;

    // Some sites use non-String objects for URLs.
    in_URL= in_URL.toString() ;

    if (u= in_URL.match(/^(javascript\:|livescript\:)([\s\S]*)$/i))
	return [ in_URL, u[1].toLowerCase(), u[2] ] ;
    if (in_URL.match(/^\s*\#/))
	return [ in_URL, '', '', '' ,'', '', '', '', in_URL ] ;

    u= in_URL.match(/^([\w\+\.\-]+\:)?\/\/([^\/\?\#\@]*\@)?(([^\:\/\?\#]*)(\:[^\/\?\#]*)?)([^\?\#]*)([^#]*)(.*)$/) ;
    if (u==null) return ;   // if pattern doesn't match
    for (var i= 0 ; i<u.length ; i++)  if (u[i]==void 0) u[i]= '' ;
    u[1]= u[1].toLowerCase() ;
    u[2]= u[2].replace(/\@$/, '') ;
    u[3]= u[3].toLowerCase() ;
    u[3]= u[3].replace(/\.+(:|$)/, '$1') ;  // close potential exploit
    u[4]= u[4].toLowerCase() ;
    u[4]= u[4].replace(/\.+$/, '') ;      // close potential exploit
    u[5]= u[5].replace(/^\:/, '') ;
    return u ;
}


// returns url_start (NOT including packed flags), packed flags, and decoded target URL.
// if in_URL is not a proxified URL, return undefined (and is legitimately used this way).
// jsm-- should clear up "return void 0" from "return [void 0, void 0, void 0]",
//   as this is called from elsewhere
function _proxy_jslib_parse_full_url(in_URL) {
    if (typeof(in_URL)=='number') in_URL= in_URL.toString() ;
    if (in_URL==void 0) return [void 0, void 0, void 0] ;
    if (in_URL=='about:blank') return ['', '', 'about:blank'] ;
    if (in_URL.match(/^(javascript|livescript)\:/i)) return ['', '', in_URL] ;
    if (in_URL.match(/^\s*\#/)) return ['', '', in_URL] ;
    if (in_URL=='') return ['', '', ''] ;

    var cmp, path_cmp ;

    if (_proxy_jslib_PROXY_GROUP.length) {
	for (var i in _proxy_jslib_PROXY_GROUP) {
	    if (in_URL.substring(0,_proxy_jslib_PROXY_GROUP[i].length)==_proxy_jslib_PROXY_GROUP[i]) {
		path_cmp= in_URL.substring(_proxy_jslib_PROXY_GROUP[i].length).match(/\/([^\/\?]*)\/?([^\?]*)(\??.*)/) ;
//		if (path_cmp==null) alert("CGIProxy Error: Can't parse URL <"+in_URL+"> with PROXY_GROUP; not setting all variables correctly.") ;
		if (path_cmp==null) return void 0 ;
		return [_proxy_jslib_PROXY_GROUP[i],
			path_cmp[1],
			_proxy_jslib_wrap_proxy_decode(path_cmp[2])+path_cmp[3]] ;
	    }
	}
	return void 0 ;
    }

    // this could be simplified....
    cmp= in_URL.match(/^([\w\+\.\-]+)\:\/\/([^\/\?]*)([^\?]*)(\??.*)$/) ;
    if (cmp==null) return void 0 ;

    // hack to canonicalize "%7e" to "~"; should do other encoded chars too
    //   as long as replacing doesn't change semantics
    cmp[3]=cmp[3].replace(/\%7e/gi, '~') ;

    path_cmp= cmp[3].match(_proxy_jslib_RE_FULL_PATH) ;
//    if (cmp==null || path_cmp==null) alert("CGIProxy Error: Can't parse URL <"+in_URL+">; not setting all variables correctly.") ;
    if (cmp==null || path_cmp==null) return void 0 ;

    return [cmp[1]+"://"+cmp[2]+path_cmp[1],
	    path_cmp[2],
	    _proxy_jslib_wrap_proxy_decode(path_cmp[3])+cmp[4]] ;
}


function _proxy_jslib_pack_flags(flags) {
    var total= 0 ;
    for (var i= 0 ; i<6 ; i++) { total= (total<<1) + !!flags[i] }
    return ''+_proxy_jslib_ARRAY64[total]+_proxy_jslib_ARRAY64[_proxy_jslib_MIME_TYPE_ID[flags[6]]] ;
}

function _proxy_jslib_unpack_flags(flagst) {
    var ret= [] ;
    var chars= flagst.split('') ;
    var total= _proxy_jslib_UNARRAY64[chars[0]] ;
    for (var i= 0 ; i<6 ; i++) { ret[5-i]= (total>>i) & 1 }
    ret[6]= _proxy_jslib_ALL_TYPES[_proxy_jslib_UNARRAY64[chars[1]]] ;
    return ret ;
}



function _proxy_jslib_html_escape(s) {
    if (s==void 0) return '' ;
    s= s.replace(/\&/g, '&amp;') ;
    s= s.replace(/([^\x00-\x7f])/g,
		 function (a) {
		     return '&#' + a.charCodeAt(0) + ';' ;
		 } ) ;
    return s.replace(/\"/g, '&quot;')
	    .replace(/\</g, '&lt;')
	    .replace(/\>/g, '&gt;') ;
}

function _proxy_jslib_html_unescape(s) {
    if (s==void 0) return '' ;
    s= s.replace(/\&\#(x)?(\w+);?/g,
		 function (a, p1, p2) { return p1
		     ? String.fromCharCode(eval('0x'+p2))
		     : String.fromCharCode(p2)
		 } ) ;
    return s.replace(/\&quot\b\;?/g, '"')
	    .replace(/\&lt\b\;?/g,   '<')
	    .replace(/\&gt\b\;?/g,   '>')
	    .replace(/\&amp\b\;?/g,  '&') ;
}



// The replace() method in Netscape is broken, :( :( so we have to implement
//   our own.  The bug is that if a function is used as the replacement pattern
//   (needed for anything complex), then *any* replace() or match() (and others?)
//   within that function (or in called functions) will cause its $' to
//   be used in place of the calling replace()'s $' .  :P
// Call this function with a string, a NON-GLOBAL (!) pattern with possible
//   parentheses, and a callback function that takes one argument that is the
//   array resulting from s.match(pattern), and returns a replacement string.
// Because of how this is implemented, ^ in pattern works much like Perl's \G.
// Because this is slower than String.replace(), avoid using this when not
//   needed, e.g. when the replacement function has no replace() or match().
function _proxy_jslib_global_replace(s, pattern, replace_function) {
    if (s==null) return s ;
    var out= '' ;
    var m1 ;
    while ((m1=s.match(pattern))!=null) {
	out+= s.substr(0,m1.index) + replace_function(m1) ;
	s= s.substr(m1.index+m1[0].length) ;
    }
    return out+s ;
}



//----------------------------------------------------------------------


EOF
    } # end setting of $JSLIB_BODY


    print $STDOUT "$HTTP_1_X 200 OK\015\012",
		  "Expires: $expires_header\015\012",
		  "Date: $date_header\015\012",
		  "Content-Type: application/x-javascript\015\012",
		  "Content-Length: ", length($JSLIB_BODY), "\015\012",
		  "\015\012",
		  $JSLIB_BODY ;

    goto ONE_RUN_EXIT ;
}




#-----------------------------------------------------------------------
#  support for proxifying ShockWave Flash (SWF) files
#-----------------------------------------------------------------------

# Given a SWF resource in $in, return the proxified version of it.
# The format of SWF files used here is described in the document "SWF and FLV
#   File Format Specification, Version 9" from Adobe, and is downloadable from
#   their site.
# jsm-- handle FileAttributes tag?
sub proxify_swf {
    my($in)= @_ ;
    my(@out, $tag, $tags) ;
    my($DONT_COMPRESS)= 0 ;   # set to 1 for testing

    # Hack to pretend it's an SWF 8 file, so we can call ExternalInterface.
    substr($in, 3, 1)= "\x08"  if substr($in, 3, 1) eq "\x07" ;

    my($swf_version, $swf_header_start, $swf_header_end, $rest)=
	&get_swf_header_and_tags($in) ;

    $tags= &proxify_swf_taglist(\$rest, $swf_version) ;

    # Set length field
    substr($swf_header_start, 4)=
	pack('V', length($swf_header_start)+length($swf_header_end)+length($tags)) ;

    substr($swf_header_start, 0, 1)= 'F'  if $DONT_COMPRESS ;

    # Compress if needed
    if (substr($swf_header_start, 0, 1) eq 'C') {
	$rest= $swf_header_end . $tags ;

	eval { require IO::Compress::Deflate } ;
	if (!$@) {
	    my $zout ;
	    no warnings qw(once) ;
	    IO::Compress::Deflate::deflate(\$rest, \$zout)
		or HTMLdie("Couldn't deflate: $IO::Compress::Deflate::DeflateError") ;
	    $rest= $zout ;
	} else {
	    substr($swf_header_start, 0, 1)= 'F' ;  # use uncompressed instead
	}

	return $swf_header_start . $rest ;
    }

    return $swf_header_start . $swf_header_end . $tags ;

}


# Given an input buffer $$in, read and process tags one at a time.
# Returns a joined string of proxified tags.
sub proxify_swf_taglist {
    my($in, $swf_version)= @_ ;
    my (@out, $tag) ;

    # Process one tag at a time
    while ($$in=~ /\G(..)/gcs) {

	# Handle short or long RECORDHEADER
	my($tag_code_and_length_code)= $1 ;
	my($tag_code_and_length_int)= unpack('v', $tag_code_and_length_code) ;
	my($tag_code)= $tag_code_and_length_int >> 6 ;
	my($tag_length)= $tag_code_and_length_int & 0x3f ;
	if ($tag_length==0x3f) {
	    $$in=~ /\G(....)/gcs ;
	    $tag_length= $1 ;
	    $tag_code_and_length_code.= $tag_length ;
	    $tag_length= unpack('V', $tag_length) ;
	}
#warn "tag code, length=[$tag_code][$tag_length]\n" ;


	# Handle ImportAssets and ImportAssets2 tags
	if ($tag_code==57 or $tag_code==71) {
	    $$in=~ /\G(.*?)\0/gcs ;
	    my($swf_URL)= $1 ;
	    my($rest_len)= $tag_length - length($swf_URL) - 1 ;
	    my($tag_rest)= substr($$in, pos($$in), $rest_len) ;
	    pos($$in)+= $rest_len ;
	    $tag= &pack_swf_tag($tag_code, &full_url($swf_URL)."\0".$tag_rest) ;

	# Handle DoAction tag
	} elsif ($tag_code==12) {
	    $tag= &pack_swf_tag(12, &proxify_swf_action_list($in, $tag_length)) ;
#warn "in DoAction; out=[".swf2perl($tag)."]\n" ;

	# Handle DoInitAction tag
	} elsif ($tag_code==59) {
	    my($sprite_id)= substr($$in, pos($$in), 2) ;
	    pos($$in)+= 2 ;
	    $tag= &pack_swf_tag(59, $sprite_id.&proxify_swf_action_list($in, $tag_length-2)) ;

	# Handle DefineSprite tag, which may contain other tags.
	} elsif ($tag_code==39) {
	    # jsm-- this could be sped up if needed...
	    $$in=~ /\G(....)/gcs ;
	    my($tag_start)= $1 ;
	    my($rest_len)= $tag_length-4 ;
	    my($taglist)= substr($$in, pos($$in), $rest_len) ;
	    pos($$in)+= $rest_len ;
	    my($tag_content)= &proxify_swf_taglist(\$taglist, $swf_version) ;
	    $tag= &pack_swf_tag(39, $tag_start . $tag_content) ;


	# Handle PlaceObject2 tag, which may contain actions
	} elsif ($tag_code==26) {
	    $$in=~ /\G(.)../gcs ;
	    my($flags)= ord($1) ;
	    if (!($flags & 0x80)) {
		my($tag_content)= substr($$in, pos($$in)-3, $tag_length) ;
		pos($$in)+= $tag_length-3 ;
		$tag= &pack_swf_tag(26, $tag_content) ;
	    } else {
		my(@out) ;   # local copy
		push(@out, substr($$in, pos($$in)-3, 3)) ;
		$$in=~ /\G(..)/gcs, push(@out, $1)    if ($flags & 2) ;
		push(@out, &get_matrix($in))          if ($flags & 4) ;
		push(@out, &get_cxformwithalpha($in)) if ($flags & 8) ;
		$$in=~ /\G(..)/gcs, push(@out, $1)    if ($flags & 16) ;
		$$in=~ /\G(.*?\0)/gcs, push(@out, $1) if ($flags & 32) ;
		$$in=~ /\G(..)/gcs, push(@out, $1)    if ($flags & 64) ;
		push(@out, &get_clip_actions($in, $swf_version)) ;
		$tag= &pack_swf_tag(26, join('', @out)) ;
	    }

	# Handle PlaceObject3 tag, which may contain actions.
	} elsif ($tag_code==70) {
	    $$in=~ /\G(..)(..)/gcs ;
	    my($flags, $depth)= (unpack('S', $1), $2) ;
	    if (!($flags & 0x8000)) {
		my($tag_content)= substr($$in, pos($$in)-4, $tag_length) ;
		pos($$in)+= $tag_length-4 ;
		$tag= &pack_swf_tag(70, $tag_content) ;
	    } else {
		my(@out) ;   # local copy
		push(@out, substr($$in, pos($$in)-4, 4)) ;
		$$in=~ /\G(.*?\0)/gcs, push(@out, $1)
		    if ($flags & 8) or (($flags & 16) and ($flags & 0x200)) ;
		$$in=~ /\G(..)/gcs, push(@out, $1)    if ($flags & 0x200) ;
		push(@out, &get_matrix($in))          if ($flags & 0x400) ;
		push(@out, &get_cxformwithalpha($in)) if ($flags & 0x800) ;
		$$in=~ /\G(..)/gcs, push(@out, $1)    if ($flags & 0x1000) ;
		$$in=~ /\G(.*?\0)/gcs, push(@out, $1) if ($flags & 0x2000) ;
		$$in=~ /\G(..)/gcs, push(@out, $1)    if ($flags & 0x4000) ;
		push(@out, &get_filterlist($in))      if ($flags & 1) ;
		$$in=~ /\G(.)/gcs, push(@out, $1)     if ($flags & 2) ;
		push(@out, &get_clip_actions($in,  $swf_version)) ;
		$tag= &pack_swf_tag(70, join('', @out)) ;
	    }


	# Handle DefineButton tag, which may contain actions
	} elsif ($tag_code==7) {
	    $$in=~ /\G(..)/gcs ;
	    my($tag_start)= $1 ;
	    my($buttonrecords)= &get_button_records($in) ;
	    my($actions)= &proxify_swf_action_list($in, $tag_length-length($buttonrecords)-3) ;
	    $tag= &pack_swf_tag(7, $tag_start.$buttonrecords.$actions) ;


	# Handle DefineButton2 tag, which may contain actions
	} elsif ($tag_code==34) {
	    my(@out) ;
	    $$in=~ /\G(...)(..)/gcs ;
	    my($tag_start, $action_offset)= ($1, unpack('v', $2)) ;
	    push(@out, $1, $2) ;
	    if ($action_offset) {
		push(@out, substr($$in, pos($$in), $action_offset-2)) ;
		pos($$in)+= $action_offset-2 ;
		push(@out, &get_buttoncondactions($in)) ;
	    } else {
		push(@out, substr($$in, pos($$in), $tag_length-5)) ;
		pos($$in)+= $tag_length-5 ;
	    }
	    $tag= &pack_swf_tag(34, join('', @out)) ;


	# Handle DoABC tag, including spawning an RTMP proxy
	} elsif ($tag_code==82) {
	    $tag= &pack_swf_tag(82, &proxify_swf_abcFile($in, $tag_length)) ;
	    if ($ALLOW_RTMP_PROXY and !$RTMP_SERVER_PORT) {
		my($LOCK_FH, $port)= create_server_lock('rtmp.run') ;
		if ($LOCK_FH) {
		    my($RTMP_LISTEN) ;
		    ($RTMP_LISTEN, $RTMP_SERVER_PORT)= new_server_socket(1935) ;
		    spawn_generic_server($RTMP_LISTEN, $LOCK_FH, \&rtmp_proxy, 600) ;
		} else {
		    $RTMP_SERVER_PORT= $port ;
		}
	    }
	    #die "DoABC tag not supported yet" ;


	} else {
	    $tag= $tag_code_and_length_code . substr($$in, pos($$in), $tag_length) ;
	    pos($$in)+= $tag_length ;
	}


	push(@out, $tag) ;

	last if $tag_code==0 ;
    }

    return join('', @out) ;
}


# Given a tag code and content, repackage a tag with correct length and format.
sub pack_swf_tag {
    my($tag_code, $tag_content)= @_ ;
    my($len)= length($tag_content) ;
    if ($len<=62) {
	return pack('v', ($tag_code<<6) + $len) . $tag_content ;
    } else {
	return pack('vV', ($tag_code<<6) + 0x3f, $len) . $tag_content ;
    }
}



# Reads zero or more BUTTONRECORDs from the input buffer, including the end flag,
#   and returns them as one string.
sub get_button_records {
    my($in, $expected_len, $in_define_button2)= @_ ;
    my($end_pos)= pos($$in)+$expected_len-1 ;

    my(@out) ;
    while (defined($expected_len) ? (pos($$in)<$end_pos)  : 1) {
	$$in=~ /\G(.)/gcs ;
	my($flags, $tag_start)= (ord($1), $1) ;
	pos($$in)--, last  if !defined($expected_len) and $flags==0 ;
	$$in=~ /\G(....)/gcs ;
	$tag_start.= $1 ;
	push(@out, $tag_start) ;
	push(@out, &get_matrix($in)) ;
	push(@out, &get_cxformwithalpha($in)) if $in_define_button2 ;
	push(@out, &get_filterlist($in))      if $in_define_button2 && ($flags & 16) ;
	$$in=~ /\G(.)/gcs, push(@out, $1)     if $in_define_button2 && ($flags & 32) ;
    }
    $$in=~ /\G\0/gcs or die "ERROR: missing end of button records" ;
    return join('', @out)."\0" ;
}


sub get_buttoncondactions {
    my($in)= @_ ;

    my(@out) ;
    while ($$in=~ /\G(..)/gcs) {
	my($action_size)= unpack('v', $1) ;
	$$in=~ /\G(..)/gcs ;
	my($flags)= $1 ;
	my($actions)= &proxify_swf_action_list($in, ($action_size>0)  ? $action_size-4  : undef) ;
	$action_size= 4+length($actions) if $action_size>0 ;
	push(@out, pack('v', $action_size), $flags, $actions) ;
	last if $action_size==0 ;
    }
    return join('', @out) ;
}



sub get_filterlist {
    my($in)= @_ ;
    my(@out) ;

    $$in=~ /\G(.)/gcs ;
    my($num_filters)= ord($1) ;
    for (1..$num_filters) {
	push(@out, &get_filter($in)) ;
    }
    return chr($num_filters).join('', @out) ;
}


sub get_filter {
    my($in)= @_ ;
    my($ret, $size) ;

    $$in=~ /\G(.)/gcs ;
    $ret= $1 ;
    my($filter_id)= $1 ;
    if ($filter_id==0) {            # DropShadowFilter
	$size= 23 ;
    } elsif ($filter_id==1) {     # BlurFilter
	$size= 9 ;
    } elsif ($filter_id==2) {     # GlowFilter
	$size= 15 ;
    } elsif ($filter_id==3) {     # BevelFilter
	$size= 27 ;
    } elsif ($filter_id==4) {     # GradientGlowFilter
	$$in=~ /\G(.)/gcs ;
	$ret.= $1 ;
	my($num_colors)= ord($1) ;
	$size= $num_colors*5 + 19 ;
    } elsif ($filter_id==5) {     # ConvolutionFilter
	$$in=~ /\G(.)(.)/gcs ;
	$ret.= $1.$2 ;
	my($matrixx, $matrixy)= (ord($1), ord($2)) ;
	$size= $matrixx*$matrixy*4 + 15 ;
    } elsif ($filter_id==6) {     # ColorMatrixFilter
	$size= 80 ;
    } elsif ($filter_id==7) {     # GradientBevelFilter
	$$in=~ /\G(.)/gcs ;
	$ret.= $1 ;
	my($num_colors)= ord($1) ;
	$size= $num_colors*5 + 19 ;
    } else {
	die "ERROR: unsupported filter type $filter_id\n" ;
    }

    $ret.= substr($$in, pos($$in), $size) ;
    pos($$in)+= $size ;
    return $ret ;
}


# Reads a CXFORMWITHALPHA record from the input buffer and returns it.
sub get_cxformwithalpha {
    my($in)= @_ ;
    my($byte1)= ord(substr($$in, pos($$in), 1)) ;
    my($has_adds)= !!($byte1 & 128) ;
    my($has_mults)= !!($byte1 & 64) ;
    my($nbits)= ($byte1>>2) & 0x0f ;
    my($record_size)= (6 + $has_adds*4*$nbits + $has_mults*4*$nbits +7)>>3 ;
    my($ret)= substr($$in, pos($$in), $record_size) ;
    pos($$in)+= $record_size ;
    return $ret ;
}


# Reads a MATRIX record from the input buffer, and returns it.
# Unfortunately, vec() uses bits in wrong order to use here, so we use the
#   function v() to reverse the bits.
# jsm-- is there an efficient way to write this routine??
sub get_matrix {
    my($in)= @_ ;
    $$in=~ /\G(.)/gcs ;
    my($in_bitbuf)= $1 ;
    my($bitpos) ;     # first byte is 0-7

    if (vec($in_bitbuf, v(0), 1)) {    # HasScale field
	$bitpos= 1 ;
	my($nbits)= ord($in_bitbuf & "\x7f")>>2 ;
	my($nbytes)= (($nbits*2)-2+7)>>3 ;
	$in_bitbuf.= substr($$in, pos($$in), $nbytes) ;
	pos($$in)+= $nbytes ;
	$bitpos+= 5+$nbits*2 ;
    } else {
	$bitpos= 1 ;
    }

    if (vec($in_bitbuf, v($bitpos), 1)) {   # HasRotate field
	$bitpos++ ;
	# Next 5 bits contain field length
	if ($bitpos+5>8*length($in_bitbuf)) {
	    $in_bitbuf.= substr($$in, pos($$in), 1) ;
	    pos($$in)++ ;
	}
	# there's got to be a better way....
	my($nbits)= vec($in_bitbuf, v($bitpos), 1)  *16
		  + vec($in_bitbuf, v($bitpos+1), 1)*8
		  + vec($in_bitbuf, v($bitpos+2), 1)*4
		  + vec($in_bitbuf, v($bitpos+3), 1)*2
		  + vec($in_bitbuf, v($bitpos+4), 1)*1 ;
	$bitpos+= 5 ;
	my($nbytes)= ($nbits*2-(length($in_bitbuf)*8-$bitpos)+7)>>3 ;
	$in_bitbuf.= substr($$in, pos($$in), $nbytes) ;
	pos($$in)+= $nbytes ;
	$bitpos+= $nbits*2 ;
    } else {
	$bitpos++ ;
    }

    # Next 5 bits contain field length
    if ($bitpos+5>8*length($in_bitbuf)) {
	$in_bitbuf.= substr($$in, pos($$in), 1) ;
	pos($$in)++ ;
    }
    my($nbits)= vec($in_bitbuf, v($bitpos), 1)  *16
	      + vec($in_bitbuf, v($bitpos+1), 1)*8
	      + vec($in_bitbuf, v($bitpos+2), 1)*4
	      + vec($in_bitbuf, v($bitpos+3), 1)*2
	      + vec($in_bitbuf, v($bitpos+4), 1)*1 ;
    $bitpos+= 5 ;
    my($nbytes)= ($nbits*2-(length($in_bitbuf)*8-$bitpos)+7)>>3 ;
    $in_bitbuf.= substr($$in, pos($$in), $nbytes) ;
    pos($$in)+= $nbytes ;

    return $in_bitbuf ;


    # Map bit positions into vec() offsets, i.e. reverse positions within byte.
    sub v {
	my($vec)= @_ ;
	return (($vec>>3)<<3) + 7-($vec & 7) ;
    }
}



# Reads SWF input, and returns the SWF header start, the SWF header end, and
#   the list of tags.  The SWF header end and the tags may be compressed,
#   together.
sub get_swf_header_and_tags {
    my($in)= @_ ;

    # Grab initial, non-compressed 8 bytes from $in
    my($header_start)= substr($in, 0, 8) ;
    my($rest)= substr($in, 8) ;
    my($sig_byte, $swf_version, $swf_length)=
	$header_start=~ /^([CF])WS(.)(....)$/s ;
    return undef unless $sig_byte ;
    $swf_version= ord($swf_version) ;
    $swf_length= unpack('V', $swf_length) ;

    # Decompress remainder of input if needed.
    if ($sig_byte eq 'C') {
	eval { require IO::Uncompress::Inflate } ;
	&no_gzip_die if $@ ;
	my $zout ;
	no warnings qw(once) ;
	IO::Uncompress::Inflate::inflate(\$rest, \$zout)
	    or HTMLdie("Couldn't inflate: $IO::Uncompress::Inflate::InflateError") ;
	$rest= $zout ;
    }

    return undef unless $swf_length==(length($rest)+8) ;

    # Calculate length of FrameSize (RECT structure) in header
    my($nbits)= ord($rest)>>3 ;
    my($totalbits)= (5+$nbits*4) ;
    my($nbytes)= ($totalbits + 7)>>3 ;

    # Grab final parts of SWF header
    my($header_end)= substr($rest, 0, $nbytes+4) ;
    substr($rest, 0, $nbytes+4)= '' ;

    return ($swf_version, $header_start, $header_end, $rest) ;
}



# Get and proxify a CLIPACTIONS record from the input buffer.
sub get_clip_actions {
    my($in, $swf_version)= @_ ;
    my($eventflags_re)= ($swf_version<=5)  ? (qr/\G(..)/s)  : (qr/\G(....)/s) ;
    my(@out) ;

    $$in=~ /\G\0\0/gc  or die "ERROR: didn't get clipaction header\n" ;
    $$in=~ /$eventflags_re/gc ;         # AllEventFlags field
    push(@out, "\0\0", $1) ;
    while ($$in=~ /$eventflags_re/gc) {
	my($event_flags)= $1 ;      # EventFlags field
	push(@out, $event_flags) ;
	last if $event_flags eq "\0\0" or $event_flags eq "\0\0\0\0" ;
	$$in=~ /\G(....)/gcs ;
	my($action_record_size)= unpack('V', $1) ;

	# If ClipEventKeyPress event is set, then process KeyCode
	my($key_code) ;
	if ($swf_version>=6 and ord(substr($event_flags, 2, 1)) & 2) {
	    $$in=~ /\G(.)/gcs ;
	    $key_code= $1 ;
	}
	my($actions)= &proxify_swf_action_list($in, $action_record_size) ;
	$action_record_size= pack('V', length($key_code)+length($actions)) ;
	push(@out, $action_record_size, $key_code, $actions) ;
    }

    return join('', @out) ;
}



# Given an input buffer, read an action list, proxify it, and return it.
sub proxify_swf_action_list {
    my($in, $action_record_size)= @_ ;
    my(@out, $out_bytes, $out, $action, $needs_swflib, @jumps, @insertions, @code_blocks) ;

    my($insert_proxify_top_url)= "\x96\$\0\cG\0\0\0\0\0_proxy_swflib_proxify_top_url\0=" ;
    my($insert_proxify_top_url_len)= length($insert_proxify_top_url) ;
    my($insert_proxify_2nd_url)= "\x96\$\0\cG\0\0\0\0\0_proxy_swflib_proxify_2nd_url\0=" ;
    my($insert_proxify_2nd_url_len)= length($insert_proxify_2nd_url) ;
    my($insert_pre_method)= "\x96\x1f\0\cG\0\0\0\0\0_proxy_swflib_pre_method\0=" ;
    my($insert_pre_method_len)= length($insert_pre_method) ;
    my($insert_pre_function)= "\x96!\0\cG\0\0\0\0\0_proxy_swflib_pre_function\0=" ;
    my($insert_pre_function_len)= length($insert_pre_function) ;

    my($start_pos)= pos($$in) ;

    while ($$in=~ /\G(.)/gcs) {
	my($action_code)= ord($1) ;
	last if $action_code==0 ;
	my($action_length, $action_content) ;
	if ($action_code>=0x80) {
	    $$in=~ /\G(..)/gcs ;
	    $action_length= unpack('v', $1) ;
	    $action_content=
		substr($$in, pos($$in), $action_length) ;
	    pos($$in)+= $action_length ;
	}

	# ActionGetURL
	if ($action_code==0x83) {
	    $action_content=~ /\G(.*?)(\0.*)$/gcs ;
	    my($action_URL, $action_rest)= ($1, $2) ;
	    # Don't proxify "javascript:" URLs.
	    if ($action_URL!~ /^\s*(?:javascript|livescript)\b/i) {
		my($old_len)= length($action_content) ;
		$action_content= &full_url($action_URL) . $action_rest ;
		my($size_diff)= length($action_content) - $old_len ;
		&update_previous_jumps(\@jumps, $out_bytes, $size_diff) ;
		&update_previous_code_blocks(\@code_blocks, $out_bytes, $size_diff) ;
		push(@insertions, { 'location' => $out_bytes , 'size' => $size_diff } ) ;
	    }
	    $action= "\x83" . pack('v', length($action_content)) . $action_content ;

	# ActionGetURL2
	} elsif ($action_code==0x9a) {
	    $needs_swflib= 1 ;
	    &update_previous_jumps(\@jumps, $out_bytes, $insert_proxify_2nd_url_len) ;
	    &update_previous_code_blocks(\@code_blocks, $out_bytes, $insert_proxify_2nd_url_len) ;
	    push(@insertions, { 'location' => $out_bytes,
				'size' => $insert_proxify_2nd_url_len } ) ;
	    push(@out, $insert_proxify_2nd_url) ;
	    $out_bytes+= $insert_proxify_2nd_url_len ;
	    $action= "\x9a" . pack('v', length($action_content)) . $action_content ;

	# ActionCallMethod
	} elsif ($action_code==0x52) {
	    $needs_swflib= 1 ;
	    &update_previous_jumps(\@jumps, $out_bytes, $insert_pre_method_len) ;
	    &update_previous_code_blocks(\@code_blocks, $out_bytes, $insert_pre_method_len) ;
	    push(@insertions, { 'location' => $out_bytes,
				'size' => $insert_pre_method_len } ) ;
	    push(@out, $insert_pre_method) ;
	    $out_bytes+= $insert_pre_method_len ;
	    $action= "\x52" ;

	# ActionCallFunction
	} elsif ($action_code==0x3d) {
	    $needs_swflib= 1 ;
	    &update_previous_jumps(\@jumps, $out_bytes, $insert_pre_function_len) ;
	    &update_previous_code_blocks(\@code_blocks, $out_bytes, $insert_pre_function_len) ;
	    push(@insertions, { 'location' => $out_bytes,
				'size' => $insert_pre_function_len } ) ;
	    push(@out, $insert_pre_function) ;
	    $out_bytes+= $insert_pre_function_len ;
	    $action= "\x3d" ;

	# ActionJump and ActionIf
	} elsif ($action_code==0x99 or $action_code==0x9d) {
	    $action= chr($action_code) . "\x02\0\0\0" ;
	    # unpack little-endian unsigned short and convert to signed short
	    my($offset)= unpack('s', pack('S', unpack('v', $action_content))) ;
	    my($jump)= { 'location' => $out_bytes,
			 'target' => $out_bytes+$offset+5 } ;
	    &handle_previous_insertions(\@insertions, $jump) ;
	    push(@jumps, $jump) ;

	# ActionDefineFunction and ActionDefineFunction2
	} elsif ($action_code==0x9b or $action_code==0x8e) {
	    my($codesize_loc)= $out_bytes+3+$action_length-2 ;
	    my($codesize)= unpack('v', substr($action_content, -2)) ;
	    push(@code_blocks, { 'code_start' => $out_bytes+3+$action_length,
				 'codesize_loc' => $codesize_loc,
				 'codesize' => $codesize } ) ;
	    $action= chr($action_code) . pack('v', length($action_content)) . $action_content ;

	# ActionTry
	} elsif ($action_code==0x8f) {
	    $action_content=~ /\G(.)(......)/gcs ;
	    my($flags)= ord($1) ;
	    my($try_size, $catch_size, $finally_size)= unpack('vvv', $2) ;
	    my($catch_nr) ;
	    if ($flags & 4) {
		$action_content=~ /\G(.)/gcs ;
		$catch_nr= $1 ;
	    } else {
		$action_content=~ /\G(.*?\0)/gcs ;
		$catch_nr= $1 ;
	    }
	    push(@code_blocks, { 'code_start' => $out_bytes + $action_length,
				 'codesize_loc' => $out_bytes+4,
				 'codesize' => $try_size } ) ;
	    push(@code_blocks, { 'code_start' => $out_bytes + $action_length
						 + $try_size,
				 'codesize_loc' => $out_bytes+6,
				 'codesize' => $catch_size } ) ;
	    push(@code_blocks, { 'code_start' => $out_bytes + $action_length
						 + $try_size + $catch_size,
				 'codesize_loc' => $out_bytes+8,
				 'codesize' => $finally_size } ) ;
	    $action= "\x8f" . pack('v', length($action_content)) . $action_content ;


	# ActionWith
	# Note that we don't "handle" it other than updating the block size.
	} elsif ($action_code==0x94) {
	    my($codesize_loc)= $out_bytes+3 ;
	    my($codesize)= unpack('v', $action_content) ;
	    push(@code_blocks, { 'code_start' => $out_bytes+5,
				 'codesize_loc' => $codesize_loc,
				 'codesize' => $codesize } ) ;
	    $action= "\x94\x02\0" . $action_content ;


	} else {
	    $action= chr($action_code)
		   . (($action_code>=0x80)
		      ? (pack('v', length($action_content)) . $action_content)
		      : '') ;
	}

	push(@out, $action) ;
	$out_bytes+= length($action) ;
    }

    $out= join('', @out) ;

    die "ERROR: out_bytes not set correctly\n" if $out_bytes!=length($out) ; 
    die "ERROR: read wrong number of bytes (expected $action_record_size, got ".(pos($$in)-$start_pos).")\n"
	if defined($action_record_size) and pos($$in)-$start_pos!=$action_record_size ;

    &rewrite_jumps(\$out, \@jumps) ;
    &rewrite_codesizes(\$out, \@code_blocks) ;

    # For now, insert $swflib at start of every tag that needs it.  Can
    #   functions in one tag be called from functions in another?
    if ($needs_swflib) {
	$swflib||= &return_swflib() ;
	$out= $swflib . $out ;
    }

    return $out."\0" ;

    #-------------------------------------

    # Update targets of already-encountered jumps, if appropriate.
    sub update_previous_jumps {
	my($jumps, $insert_pos, $offset)= @_ ;
	foreach (@$jumps) {
	    $_->{target}+= $offset  if $_->{target} > $insert_pos ;
	}
    }

    # Update codeSize fields in DefineFunction2 actions
    sub update_previous_code_blocks {
	my($code_blocks, $insert_pos, $offset)= @_ ;
	foreach (@$code_blocks) {
	    $_->{codesize}+= $offset
		if     ($_->{code_start} <= $insert_pos)
		    && ($_->{code_start}+$_->{codesize} > $insert_pos) ;
	}
    }

    # Update the current jump's target, based on previous insertions.
    sub handle_previous_insertions {
	my($insertions, $jump)= @_ ;
	foreach (reverse @$insertions) {
	    $jump->{target}-= $_->{size}
		if $_->{location}+$_->{size} >= $jump->{target} ;
	}
    }

    # Rewrite offsets of all jumps in @out.
    sub rewrite_jumps {
	my($out, $jumps)= @_ ;
	foreach (@$jumps) {
	    die "ERROR: jump is not a jump\n"
		if substr($$out, $_->{location}, 1)!~ /^[\x99\x9d]/ ;
	    # pack signed short back into little-endian unsigned short
	    substr($$out, $_->{location}+3, 2)=
		pack('v', unpack('S', pack('s', $_->{target} - $_->{location} - 5))) ;  # jump actions are 5 bytes
	}
    }

    # Rewrite codeSize fields in DefineFunction2 actions
    sub rewrite_codesizes {
	my($out, $code_blocks)= @_ ;
	foreach (@$code_blocks) {
	    substr($$out, $_->{codesize_loc}, 2)= pack('v', $_->{codesize}) ;
	}
    }

}



# This is the ActionScript VM bytecode of the library needed to proxify SWF.
#   files.  See the file "swflib.asm" for the commented assembler code.
sub return_swflib {

    return "\x8e\x1f\0_proxy_swflib_alert_top\0\0\0\0*\x002\0L\x96\cY\0\0javascript:alert(\"top=[\0MG\x96\cE\0\0]\")\0G\x96\cB\0\0\0\x9a\cA\0\0>\x8e\$\0_proxy_swflib_set_classlists\0\0\0\0*\0\x7f\cB\x96\cF\0\0load\0\x96 \0\0XML\0\0LoadVars\0\0StyleSheet\0\cG\cC\0\0\0B\x96\cJ\0\0download\0\x96\cT\0\0FileReference\0\cG\cA\0\0\0B\x96\cH\0\0upload\0\x96\cT\0\0FileReference\0\cG\cA\0\0\0B\x96\cF\0\0send\0\x96\cT\0\0XML\0\0LoadVars\0\cG\cB\0\0\0B\x96\cM\0\0sendAndLoad\0\x96\cT\0\0XML\0\0LoadVars\0\cG\cB\0\0\0B\x96\cH\0\0getURL\0\x96\cP\0\0MovieClip\0\cG\cA\0\0\0B\x96\cK\0\0loadMovie\0\x96\cP\0\0MovieClip\0\cG\cA\0\0\0B\x96\cO\0\0loadVariables\0\x96\cP\0\0MovieClip\0\cG\cA\0\0\0B\x96\cJ\0\0loadClip\0\x96\cV\0\0MovieClipLoader\0\cG\cA\0\0\0B\x96\cI\0\0connect\0\x96\cT\0\0NetConnection\0\cG\cA\0\0\0B\x96\cF\0\0play\0\x96\cP\0\0NetStream\0\cG\cA\0\0\0B\x96\cP\0\0loadPolicyFile\0\x96\cO\0\0Security\0\cG\cA\0\0\0B\x96\cK\0\0loadSound\0\x96\cL\0\0Sound\0\cG\cA\0\0\0B\x96\cE\0\cG\cM\0\0\0C\x96\cZ\0\0_proxy_swflib_classlists\0M\x1d\x96\cJ\0\0getURL\0\cE\cA\x96\cM\0\0loadMovie\0\cE\cA\x96\cP\0\0loadMovieNum\0\cE\cA\x96\cQ\0\0loadVariables\0\cE\cA\x96\cT\0\0loadVariablesNum\0\cE\cA\x96\cE\0\cG\cE\0\0\0C\x96\x1c\0\0_proxy_swflib_functionlist\0M\x1d>\x96#\0\cG\0\0\0\0\0_proxy_swflib_set_classlists\0=\x8e \0_proxy_swflib_pre_method\0\0\0\0*\0\cO\cB\x96\x1b\0\0_proxy_swflib_method_name\0M\x1d\x96\cV\0\0_proxy_swflib_object\0M\x1d\x96\cZ\0\0_proxy_swflib_num_params\0M\x1d\x96\cZ\0\0_proxy_swflib_classlists\0\x1c\x96\x1b\0\0_proxy_swflib_method_name\0\x1cNL\x96\cA\0\cCI\x9d\cB\0\cS\cALD\x96\cJ\0\0function\0I\x9d\cB\0\xfe\0L\x96\cY\0\0_proxy_swflib_classlist\0M\x1d\x96\cH\0\0length\0NQ\x96\cQ\0\0_proxy_swflib_j\0M\x1d\x96\cV\0\0_proxy_swflib_object\0\x1c\x96\cY\0\0_proxy_swflib_classlist\0\x1c\x96\cQ\0\0_proxy_swflib_j\0\x1cN\x1cT\cR\x9d\cB\x000\0\x96\cE\0\cG\0\0\0\0\x96\x1f\0\0_proxy_swflib_proxify_top_url\0=\x99\cB\x008\0\x96\cQ\0\0_proxy_swflib_j\0L\x1cQ\x1d\x96\cQ\0\0_proxy_swflib_j\0\x1c\x9d\cB\0I\xff\x99\cB\0\cA\0\cW\x96\cZ\0\0_proxy_swflib_num_params\0\x1c\x96\cV\0\0_proxy_swflib_object\0\x1c\x96\x1b\0\0_proxy_swflib_method_name\0\x1c>\x8e\"\0_proxy_swflib_pre_function\0\0\0\0*\0\xf4\0\x96\x1d\0\0_proxy_swflib_function_name\0M\x1d\x96\cZ\0\0_proxy_swflib_num_params\0M\x1d\x96\x1c\0\0_proxy_swflib_functionlist\0\x1c\x96\x1d\0\0_proxy_swflib_function_name\0\x1cN\cR\x9d\cB\0+\0\x96\cE\0\cG\0\0\0\0\x96\x1f\0\0_proxy_swflib_proxify_top_url\0=\x96\cZ\0\0_proxy_swflib_num_params\0\x1c\x96\x1d\0\0_proxy_swflib_function_name\0\x1c>\x8e%\0_proxy_swflib_proxify_top_url\0\0\0\0*\0|\0L\x96\cA\0\cBI\x9d\cB\0p\0\x96\x1c\0\0_proxy_jslib_full_url\0\cG\cB\0\0\0\x96\cG\0\0flash\0\x1c\x96\cJ\0\0external\0N\x96\cS\0\0ExternalInterface\0N\x96\cF\0\0call\0RL\x96\cF\0\0null\0I\cR\x9d\cB\0\cF\0\cW\x96\cB\0\0\0>\x8e%\0_proxy_swflib_proxify_2nd_url\0\0\0\0*\0^\0\x96\cV\0\0_proxy_swflib_target\0M\x1d\x96\$\0\cG\0\0\0\0\0_proxy_swflib_proxify_top_url\0=\x96\cV\0\0_proxy_swflib_target\0\x1c>" ;

}


#----------------------------------------------------------------------
# Below is for handling SWF 9+ actions ("abcFile").  For full details,
#   see the spec at:
#   http://www.adobe.com/content/dam/Adobe/en/devnet/actionscript/articles/avm2overview.pdf
#----------------------------------------------------------------------

sub proxify_swf_abcFile {
    my($in, $record_length)= @_ ;

    # First, get fields of DoABC tag.
    $$in=~ /\G(....)(.*?\0)/gcs ;
    my($flags, $name)= ($1, $2) ;

    # Now, start the ABCData field.
    $$in=~ /\G(..)(..)/gcs ;
    my($major_ver, $minor_ver)= ($1, $2) ;

    my($cpool_info, $string_count, $multiname_count, $mn_specials)=
	&proxify_swf_cpool_info($in) ;
    my $method_infos= &get_swf_method_infos($in) ;
    my $metadata_infos= &get_swf_metadata_infos($in) ;
    my $instance_class_infos= &get_swf_instance_class_infos($in) ;
    my $script_infos= &get_swf_script_infos($in) ;
    my $method_body_infos=
	&proxify_swf_method_body_infos($in, $string_count, $multiname_count, $mn_specials) ;

    return join('', $flags, $name, $major_ver, $minor_ver,
		    $cpool_info, $method_infos, $metadata_infos, $instance_class_infos, $script_infos, $method_body_infos) ;
}


# Add our 8 strings, 3 namespaces, and 4 multinames to the constant pool.
# Note that there's a bug in Flash where the 0 namespace isn't handled
#   correctly.  The workaround is to use the empty string as the namespace,
#   meaning we need to add an empty string and a namespace that uses it.
# $n_specials is used to remember where the strings "connect" and "play" are,
#   to detect multinames that use them, so that we can proxify NetConnection.connect()
#   and NetStream.play() calls.  [Later: added "URLRequest", "loaderURL", "loadPolicyFile".]
sub proxify_swf_cpool_info {
    my($in)= @_ ;
    my(@out, $s) ;
    my $n_specials= { connect => [], play => [], URLRequest => [], loaderURL => [], loadPolicyFile => [], url => [] } ;
    my $mn_specials= { connect => [], play => [], URLRequest => [], loaderURL => [], loadPolicyFile => [], url => [] } ;

    # get all constants, then just push substr($$in, ...) .
    # First, pass through initial parts that don't change.
    my $start_pos= pos($$in) ;
    my $int_count= &get_swf_u30_32($in) ;
    &skip_swf_u30_u32_s32($in)  foreach (1..$int_count-1) ;
    my $uint_count= &get_swf_u30_32($in) ;
    &skip_swf_u30_u32_s32($in)  foreach (1..$uint_count-1) ;
    my $double_count= &get_swf_u30_32($in) ;
    # Unmentioned in the spec, double_count can be 0.
    pos($$in)+= 8*($double_count-1) if $double_count ;
    push(@out, substr($$in, $start_pos, pos($$in)-$start_pos)) ;

    # Copy through strings, adding the 16 strings we need.
    my $string_count= &get_swf_u30_32($in) ;
    push(@out, &set_swf_u30_32($string_count+16)) ;
    $start_pos= pos($$in) ;
    foreach (1..$string_count-1) {
	$s= &get_swf_string($in) ;
	push(@{$n_specials->{$s}}, $_)  if defined $n_specials->{$s} ;
    }
    push(@out, substr($$in, $start_pos, pos($$in)-$start_pos)) ;
    push(@out, "\x09flash.net\x0aURLRequest\x03url\x0eflash.external\x11ExternalInterface\x15_proxy_jslib_full_url\x04call\0\x0dNetConnection\x09NetStream\x1d_proxy_jslib_full_url_connect\x1a_proxy_jslib_full_url_play\x05alert\x1d_proxy_jslib_reverse_full_url\x0dflash.display\x0aLoaderInfo") ;

    # Copy through namespace info, adding the 3 we need.
    my $ns_count= &get_swf_u30_32($in) ;
    push(@out, &set_swf_u30_32($ns_count+4)) ;
    $start_pos= pos($$in) ;
    pos($$in)++, &skip_swf_u30_u32_s32($in)  foreach (1..$ns_count-1) ;
    push(@out, substr($$in, $start_pos, pos($$in)-$start_pos)) ;
    push(@out, "\x16" . &set_swf_u30_32($string_count)       # flash.net
	     . "\x16" . &set_swf_u30_32($string_count+3)     # flash.external
	     . "\x16" . &set_swf_u30_32($string_count+7)     # ""
	     . "\x16" . &set_swf_u30_32($string_count+14)) ; # flash.display

    # Namespace sets are unchanging.
    $start_pos= pos($$in) ;
    my $ns_set_count= &get_swf_u30_32($in) ;
    &get_swf_ns_set($in)  foreach (1..$ns_set_count-1) ;
    push(@out, substr($$in, $start_pos, pos($$in)-$start_pos)) ;

    # Copy through multinames, adding the 6 multinames we need.
    # Note that $string_count is the last string ID plus one.
    my $multiname_count= &get_swf_u30_32($in) ;
    push(@out, &set_swf_u30_32($multiname_count+7)) ;
    $start_pos= pos($$in) ;
    # Note that $mn_specials is modified in get_swf_multiname().
    &get_swf_multiname($in, $_, $n_specials, $mn_specials)  foreach (1..$multiname_count-1) ;
    push(@out, substr($$in, $start_pos, pos($$in)-$start_pos)) ;
    push(@out, "\x07" . &set_swf_u30_32($ns_count)             # flash.net
		      . &set_swf_u30_32($string_count+1)       # URLRequest
	     . "\x07" . &set_swf_u30_32($ns_count+2)           # ""
		      . &set_swf_u30_32($string_count+2)       # url
	     . "\x07" . &set_swf_u30_32($ns_count+1)           # flash.external
		      . &set_swf_u30_32($string_count+4)       # ExternalInterface
	     . "\x07" . &set_swf_u30_32($ns_count+2)           # ""
		      . &set_swf_u30_32($string_count+6)       # call
	     . "\x07" . &set_swf_u30_32($ns_count)             # flash.net
		      . &set_swf_u30_32($string_count+8)       # NetConnection
	     . "\x07" . &set_swf_u30_32($ns_count)             # flash.net
		      . &set_swf_u30_32($string_count+9)       # NetStream
	     . "\x07" . &set_swf_u30_32($ns_count+3)           # flash.display
		      . &set_swf_u30_32($string_count+15)) ;   # LoaderInfo

    return (join('', @out), $string_count, $multiname_count, $mn_specials) ;
}


sub get_swf_method_infos {
    my($in)= @_ ;
    my($param_count, $flags) ;

    my $start_pos= pos($$in) ;
    my $count= &get_swf_u30_32($in) ;
    for (1..$count) {
	$param_count= &get_swf_u30_32($in) ;
	&skip_swf_u30_u32_s32($in) ;
	&skip_swf_u30_u32_s32($in)  foreach (1..$param_count) ;
	&skip_swf_u30_u32_s32($in) ;
	$$in=~ /\G(.)/gcs  && ($flags= ord($1)) ;
	&get_swf_option_info($in)  if $flags & 0x08 ;
	if ($flags & 0x80) {
	    &skip_swf_u30_u32_s32($in)  foreach (1..$param_count) ;
	}
    }

    return substr($$in, $start_pos, pos($$in)-$start_pos) ;
}


sub get_swf_metadata_infos {
    my($in)= @_ ;
    my $start_pos= pos($$in) ;
    my $mi_count= &get_swf_u30_32($in) ;
    for (1..$mi_count) {
	&skip_swf_u30_u32_s32($in) ;
	my $item_count= &get_swf_u30_32($in) ;
	&skip_swf_u30_u32_s32($in)  for (1..2*$item_count) ;  # item_info is 2 u30's
    }

    return substr($$in, $start_pos, pos($$in)-$start_pos) ;
}


sub get_swf_instance_class_infos {
    my($in)= @_ ;
    my $start_pos= pos($$in) ;
    my($flags, $intrf_count, $trait_count) ;
    my $count= &get_swf_u30_32($in) ;
    for (1..$count) {       # instance_info
	&skip_swf_u30_u32_s32($in) ;
	&skip_swf_u30_u32_s32($in) ;
	$$in=~ /\G(.)/gcs  && ($flags= ord($1)) ;
	&skip_swf_u30_u32_s32($in)  if $flags & 0x08 ;
	$intrf_count= &get_swf_u30_32($in) ;
	&skip_swf_u30_u32_s32($in)  for (1..$intrf_count) ;
	&skip_swf_u30_u32_s32($in) ;
	$trait_count= &get_swf_u30_32($in) ;
	&get_swf_traits_info($in)  for (1..$trait_count) ;
    }
    for (1..$count) {       # class_info
	&skip_swf_u30_u32_s32($in) ;
	$trait_count= &get_swf_u30_32($in) ;
	&get_swf_traits_info($in)  for (1..$trait_count) ;
    }

    return substr($$in, $start_pos, pos($$in)-$start_pos) ;
}


sub get_swf_script_infos {
    my($in)= @_ ;
    my $start_pos= pos($$in) ;
    my($trait_count) ;
    my $count= &get_swf_u30_32($in) ;
    for (1..$count) {       # script_info
	&skip_swf_u30_u32_s32($in) ;
	$trait_count= &get_swf_u30_32($in) ;
	&get_swf_traits_info($in)  for (1..$trait_count) ;
    }

    return substr($$in, $start_pos, pos($$in)-$start_pos) ;
}


# Here is where the AVM2 bytecode is proxified.
sub proxify_swf_method_body_infos {
    my($in, $string_count, $multiname_count, $mn_specials)= @_ ;
    my(@out, $pos, $code_length, $code, $insertions, $pre_coerce_ins_part1, $pre_coerce_ins_part2,
       $exception_count, $trait_count) ;

    my $count= &get_swf_u30_32($in) ;
    push(@out, &set_swf_u30_32($count)) ;

    # These are what need to be inserted into the bytecode at various points.
    # Since length may vary, must calculate length of the code after the jump(s).
    my($post_construct_ins, $pre_connect_ins, $pre_play_ins, $post_loaderURL_ins,
       $replace_get_url_ins, $proxify_top_url_ins, $after_jump, $after_jump2) ;

    my $alert_ins= "\x2a\x60" . &set_swf_u30_32($multiname_count+2)
		 . "\x2b\x2c" . &set_swf_u30_32($string_count+12)
		 . "\x2b\x46" . &set_swf_u30_32($multiname_count+3)
		 . "\x02\x29" ;

    $proxify_top_url_ins= "\x60" . &set_swf_u30_32($multiname_count+2)
		 . "\x2b\x2c" . &set_swf_u30_32($string_count+5)
		 . "\x2b\x46" . &set_swf_u30_32($multiname_count+3) . "\x02" ;


    $after_jump= "\x2a\x2a\x60" . &set_swf_u30_32($multiname_count+2)
	       . "\x2b\x2c" . &set_swf_u30_32($string_count+5)
	       . "\x2b\x66" . &set_swf_u30_32($multiname_count+1)
	       . "\x46" . &set_swf_u30_32($multiname_count+3)
	       . "\x02\x61" . &set_swf_u30_32($multiname_count+1) ;
    $post_construct_ins= "\x2a\xb2" . &set_swf_u30_32($multiname_count)
		       . "\x12" . &set_swf_s24(length($after_jump)) . $after_jump ;

    $after_jump= "\x2b\x60" . &set_swf_u30_32($multiname_count+2)
	       . "\x2b\x2c" . &set_swf_u30_32($string_count+10)
	       . "\x2b\x46" . &set_swf_u30_32($multiname_count+3) . "\x02" ;
    $pre_connect_ins= "\x2b\x2a\xb2" . &set_swf_u30_32($multiname_count+4)
		    . "\x11" . &set_swf_s24(5) . "\x2b\x10" . &set_swf_s24(length($after_jump)) . $after_jump ;

    $after_jump= "\x2b\x60" . &set_swf_u30_32($multiname_count+2)
	       . "\x2b\x2c" . &set_swf_u30_32($string_count+11)
	       . "\x2b\x46" . &set_swf_u30_32($multiname_count+3) . "\x02" ;
    $pre_play_ins= "\x2b\x2a\xb2" . &set_swf_u30_32($multiname_count+5)
		 . "\x11" . &set_swf_s24(5) . "\x2b\x10" . &set_swf_s24(length($after_jump)) . $after_jump ;

    $post_loaderURL_ins= "\x60" . &set_swf_u30_32($multiname_count+2)
		       . "\x2b\x2c" . &set_swf_u30_32($string_count+13)
		       . "\x2b\x46" . &set_swf_u30_32($multiname_count+3) . "\x02" ;

    $after_jump= "\x66" . &set_swf_u30_32($multiname_count+1)
	       . "\x60" .  &set_swf_u30_32($multiname_count+2)
	       . "\x2b\x2c" . &set_swf_u30_32($string_count+13)
	       . "\x2b\x46" . &set_swf_u30_32($multiname_count+3) . "\x02" ;
    $after_jump2= "\x66" . &set_swf_u30_32($multiname_count+1)
		. "\x10" . &set_swf_s24(length($after_jump)) ;
    $replace_get_url_ins= "\x2a\xb2" . &set_swf_u30_32($multiname_count+6)
			. "\x11" . &set_swf_s24(length($after_jump2)) . $after_jump2 . $after_jump ;

    # Calculate unchanging parts outside of loop.
    $pre_coerce_ins_part1= "\x2a\xb2" . &set_swf_u30_32($multiname_count)
			 . "\x11" ;
    $pre_coerce_ins_part2= "\x2a\x2a\x60" . &set_swf_u30_32($multiname_count+2)
			 . "\x2b\x2c" . &set_swf_u30_32($string_count+5)
			 . "\x2b\x66" . &set_swf_u30_32($multiname_count+1)
			 . "\x46" . &set_swf_u30_32($multiname_count+3)
			 . "\x02\x61" . &set_swf_u30_32($multiname_count+1)
			 . "\x10" ;

    # Handle one method body at a time
    for my $mb (0..$count-1) {
	$pos= pos($$in) ;
	&skip_swf_u30_u32_s32($in) ;
	push(@out, substr($$in, $pos, pos($$in)-$pos)) ;

	# The max_stack setting for each method has to be increased by 5.
	my $max_stack= &get_swf_u30_32($in) ;
	push(@out, &set_swf_u30_32($max_stack+5)) ;

	$pos= pos($$in) ;
	&skip_swf_u30_u32_s32($in) for 1..3 ;
	push(@out, substr($$in, $pos, pos($$in)-$pos)) ;

	# proxify the code segment!
	$code_length= &get_swf_u30_32($in) ;
	$code= substr($$in, pos($$in), $code_length) ;
	pos($$in)+= $code_length ;
	($code, $insertions)=
	    &proxify_swf_avm2_code($code, $proxify_top_url_ins, $post_construct_ins, $pre_connect_ins, $pre_play_ins,
		$post_loaderURL_ins, $replace_get_url_ins, $pre_coerce_ins_part1, $pre_coerce_ins_part2, $mn_specials, $mb, $alert_ins) ;
	push(@out, &set_swf_u30_32(length($code)), $code) ;

	# Exceptions each have three references to code positions that must be updated.
	$exception_count= &get_swf_u30_32($in) ;
	push(@out, &set_swf_u30_32($exception_count)) ;
	push(@out, &proxify_exception_info($in, $insertions)) for (1..$exception_count) ;

	$pos= pos($$in) ;
	$trait_count= &get_swf_u30_32($in) ;
	&get_swf_traits_info($in)  for (1..$trait_count) ;
	push(@out, substr($$in, $pos, pos($$in)-$pos)) ;
    }

    return join('', @out) ;
}


sub proxify_exception_info {
    my($in, $insertions)= @_ ;
    my($from, $to, $target)= (&get_swf_u30_32($in), &get_swf_u30_32($in), &get_swf_u30_32($in)) ;
    foreach my $i (@$insertions) {
	$from+=   $i->{len} if $from   >= $i->{pos} ;
	$to+=     $i->{len} if $to     >= $i->{pos} ;
	$target+= $i->{len} if $target >= $i->{pos} ;
    }
    my $ret= &set_swf_u30_32($from) . &set_swf_u30_32($to) . &set_swf_u30_32($target) ;
    my $pos= pos($$in) ;
    &skip_swf_u30_u32_s32($in) ;
    &skip_swf_u30_u32_s32($in) ;
    return $ret . substr($$in, $pos, pos($$in)-$pos) ;
}



# Here's where the code modification happens.  Inserts $post_construct_ins after
#   every construct or constructprop, $pre_connect_ins before a callpropvoid
#   that calls "connect", and $pre_play_ins before a callpropvoid that calls
#   "play".  After making all insertions, updates all jumps.
# $mn_specials is the list of which multinames refer to a name "connect", "play",
#   or one of several other strings we must catch.
sub proxify_swf_avm2_code {
    my($code, $proxify_top_url_ins, $post_construct_ins, $pre_connect_ins, $pre_play_ins, $post_loaderURL_ins,
       $replace_get_url_ins, $pre_coerce_ins_part1, $pre_coerce_ins_part2, $mn_specials, $mb, $alert_ins)= @_ ;
    my(@out, $out_len, $old_out_len, $old_code_pos, $op, @params, $param_st, $pos, $out,
       $target, @insertions, @jumps, $pre_coerce_ins, $after_jump) ;
    &set_AVM2_BYTECODES() unless $AVM2_BYTECODES ;

    my $post_construct_ins_len= length($post_construct_ins) ;
    my $pre_connect_ins_len= length($pre_connect_ins) ;
    my $pre_play_ins_len= length($pre_play_ins) ;
    my $post_loaderURL_ins_len= length($post_loaderURL_ins) ;
    my $proxify_top_url_ins_len= length($proxify_top_url_ins) ;
    my $replace_get_url_ins_len= length($replace_get_url_ins) ;

use vars qw($test) ;

    # Loop through $code, one instruction at a time.
    # jsm-- must account for $code > \xff ?
    while ($code=~ /\G(.)/gcs) {
	$op= $1 ;
	$old_code_pos= pos($code)-1 ;
	$old_out_len= $out_len ;
&HTMLdie("Bad opcode: [" . swf2perl($op) . "] at position " . $old_code_pos . " in method body $mb.")
unless defined $AVM2_BYTECODES->[ord($op)] ;    # jsm

	# Read in any parameters for this instruction.
	@params= () ;
	if ($AVM2_BYTECODES->[ord($op)]{params}) {
	    $pos= pos($code) ;
	    foreach my $f (@{ $AVM2_BYTECODES->[ord($op)]{params} }) {
		push(@params, $f->(\$code)) ;
	    }
	    $param_st= substr($code, $pos, pos($code)-$pos) ;
	} else {
	    $param_st= '' ;
	}

	# Because some insertions are before the instruction and some are
	#   after, we must push the instruction inside the conditional.

	# Insert a code bit after every contruct.
	if ($op eq "\x42") {
	    push(@out, $op, $param_st) ;
	    $out_len+= length($op)+length($param_st) ;

	    push(@insertions, {pos => $out_len, len => $post_construct_ins_len}) ;
	    push(@out, $post_construct_ins) ;
	    $out_len+= $post_construct_ins_len ;


	# Insert a code bit after every constructprop, but only if the index
	#   parameter references a "URLRequest" string.
	# jsm-- should handle runtime multinames too....
	} elsif ($op eq "\x4a") {
	    push(@out, $op, $param_st) ;
	    $out_len+= length($op)+length($param_st) ;

	    foreach (@{$mn_specials->{URLRequest}}) {
		if ($params[0]==$_) {
		    push(@insertions, {pos => $out_len, len => $post_construct_ins_len}) ;
		    push(@out, $post_construct_ins) ;
		    $out_len+= $post_construct_ins_len ;
		    last ;
		}
	    }

	# Insert a code bit before every coerce, but only if the index parameter
	#   references a "URLRequest" string.
	# Gets a bit messy avoiding double-proxifying here.
	# jsm-- should handle runtime multinames too....
	} elsif ($op eq "\x80") {
	    # Next two lines would be after block below if it worked, but
	    #   for now we'll just use $post_construct_ins instead of $pre_coerce_ins .
	    push(@out, $op, $param_st) ;
	    $out_len+= length($op)+length($param_st) ;
	    foreach (@{$mn_specials->{URLRequest}}) {
		if ($params[0]==$_) {
		    # jsm-- this could result in double-proxifying of URLs.  The
		    #   commented-out section below could solve that, but has some
		    #   bug that doesn't proxify every URL in a SWF.  So for now,
		    #   keep the privacy hole closed and risk double-proxifying some
		    #   URLs.  The downside is that either @BANNED_NETWORKS can't
		    #   include localhost, or that we disable double-proxified URLs
		    #   in _proxy_jslib_full_url(), meaning that chained accesses
		    #   through the same script won't proxify Flash correctly.
		    ## This is the part of this insertion that varies-- also messy.
		    #$after_jump= "\x80" . $param_st . $pre_coerce_ins_part2 . &set_swf_s24(1+length($param_st)) ;
		    #$pre_coerce_ins= $pre_coerce_ins_part1 . &set_swf_s24(length($after_jump)) . $after_jump ;
		    #$pre_coerce_ins= "\x2a\x12" . &set_swf_s24(length($pre_coerce_ins)) . $pre_coerce_ins ;
		    #push(@insertions, {pos => $out_len, len => length($pre_coerce_ins)}) ;
		    #push(@out, $pre_coerce_ins) ;
		    #$out_len+= length($pre_coerce_ins) ;
		    push(@insertions, {pos => $out_len, len => $post_construct_ins_len}) ;
		    push(@out, $post_construct_ins) ;
		    $out_len+= $post_construct_ins_len ;
		    last ;
		}
	    }

	# Insert a code bit before every callpropvoid, but only if the index
	#   parameter references a "connect" or "play".  We do the same for
	#   callproperty-- even though the compiler doesn't use it for
	#   NetConnection.connect() and NetStream.play(), privacy could be
	#   compromised if a malicious server uses callproperty.
	# Also, do this for callsuper and callsupervoid.
	} elsif ($op eq "\x4f" or $op eq "\x46" or $op eq "\x45" or $op eq "\x4e") {
	    my $done ;
	    foreach (@{$mn_specials->{'connect'}}) {
		if ($params[0]==$_) {
		    # connect() can have more than one param, but we wouldn't handle
		    #   that correctly with what we have.
		    if ($params[1]==1) {
			push(@insertions, {pos => $out_len, len => $pre_connect_ins_len}) ;
			push(@out, $pre_connect_ins) ;
			$out_len+= $pre_connect_ins_len ;
		    }
		    $done= 1 ;
		    last ;
		}
	    }
	    if (!$done) {
		foreach (@{$mn_specials->{play}}) {
		    if ($params[0]==$_) {
			# To avoid some false positives, require that the second param is 1.
			if ($params[1]==1) {
			    push(@insertions, {pos => $out_len, len => $pre_play_ins_len}) ;
			    push(@out, $pre_play_ins) ;
			    $out_len+= $pre_play_ins_len ;
			}
			$done= 1 ;
			last ;
		    }
		}
	    }
	    if (!$done) {
		foreach (@{$mn_specials->{loadPolicyFile}}) {
		    if ($params[0]==$_) {
			push(@insertions, {pos => $out_len, len => $proxify_top_url_ins_len}) ;
			push(@out, $proxify_top_url_ins) ;
			$out_len+= $proxify_top_url_ins_len ;
			last ;
		    }
		}
	    }

	    push(@out, $op, $param_st) ;
	    $out_len+= length($op)+length($param_st) ;


	# Record every jump, to be updated later.
	# All jump opcodes are in the range \x0c-\x1a except for lookupswitch (\x1b).
	# $jumps[]{pos} is the position of the offset parameter of the jump
	#   action, which is 3 bytes earlier than the current $out_len.
	# Note that {pos} is based on $out_len (i.e. post-processing position),
	#   while {target} and {base} are based on pos($code) (i.e.
	#   pre-processing position).
	} elsif ($op=~ /^[\x0c-\x1a]$/) {
	    push(@out, $op, $param_st) ;
	    $out_len+= length($op)+length($param_st) ;
	    push(@jumps, {pos => $out_len-3,
			  target => pos($code)+$params[0],
			  base => pos($code)}) ;

	# Handle lookupswitch, which needs special care.
	} elsif ($op eq "\x1b") {
	    push(@out, $op, $param_st) ;
	    $out_len+= length($op)+length($param_st) ;

	    # First, add the default jump.
	    push(@jumps, {pos => $old_out_len+1,
			  target => $old_code_pos+$params[0][0],
			  base => $old_code_pos}) ;
	    # Then, add all the case jumps, which come after a u30 that we must skip.
	    my $case_pos= $out_len - 3*($params[0][1]+1) ;
	    for (2..$params[0][1]+2) {
		push(@jumps, {pos => $case_pos,
			      target => $old_code_pos+$params[0][$_],
			      base => $old_code_pos}) ;
		$case_pos+= 3 ;
	    }


	# Insert a code bit before every getproperty, but only if the index
	#   parameter references a "loaderURL" (for flash.display.LoaderInfo.loaderURL)
	#   or a "url".  If "url", does a replacement rather than a prepending.
	} elsif ($op eq "\x66") {
	    my $done ;

	    foreach (@{$mn_specials->{loaderURL}}) {
		if ($params[0]==$_) {
		    push(@out, $op, $param_st) ;
		    $out_len+= length($op)+length($param_st) ;
		    push(@insertions, {pos => $out_len, len => $post_loaderURL_ins_len}) ;
		    push(@out, $post_loaderURL_ins) ;
		    $out_len+= $post_loaderURL_ins_len ;
		    $done= 1 ;
		    last ;
		}
	    }
	    if (!$done) {
		foreach (@{$mn_specials->{url}}) {
		    if ($params[0]==$_) {
			push(@insertions, {pos => $out_len, len => $replace_get_url_ins_len-length($op)-length($param_st)}) ;
			push(@out, $replace_get_url_ins) ;
			$out_len+= $replace_get_url_ins_len ;
			$done= 1 ;
			last ;
		    }
		}
	    }
	    if (!$done) {
		push(@out, $op, $param_st) ;
		$out_len+= length($op)+length($param_st) ;
	    }


	} else {
	    push(@out, $op, $param_st) ;
	    $out_len+= length($op)+length($param_st) ;
	}
    }

    $out= join('', @out) ;

    if (@insertions) {
	# Update all jump targets in place in $out.
	foreach my $j (@jumps) {
	    foreach my $i (@insertions) {
		$j->{target}+= $i->{len}  if ($j->{target} >= $i->{pos}) ;
		$j->{base}+=   $i->{len}  if ($j->{base} >= $i->{pos}) ;
	    }
	    substr($out, $j->{pos}, 3)= &set_swf_s24($j->{target} - $j->{base}) ;
	}
    }

    return ($out, \@insertions) ;
}



# Skip past variable-length integer, when we don't need the value.
sub skip_swf_u30_u32_s32 {
    ${$_[0]}=~ /\G[\x80-\xff]{0,4}[\0-\x7f]/gcs ;
    return ;
}


# u30 and u32 are var-length integers-- 1-5 bytes, each byte contributes 7 low
#   bits, ends when top bit is not set.
# Perl's pack('w') template packs a variable-length integer much like SWF's
#   u30/32, but with the byte order reversed.  So here we reverse the string,
#   then set the high bit of the first byte and clear the high bit of the last
#   byte.  Then we can use pack/unpack.
sub get_swf_u30_32 {
    my($in)= @_ ;
    return ord($1) if $$in=~ /\G([\0-\x7f])/gc ;    # shortcut for common case
    $$in=~ /\G([\x80-\xff]{0,4}[\0-\x7f])/gc ;
    my $ret= reverse $1 ;
    substr($ret, 0, 1)|= "\x80" ;
    substr($ret, -1, 1)&= "\x7f" ;
    return unpack('w', $ret) ;

#    my($total, $i) ;
#    my(@bytes)= split(//, $1) ;
#    $total+= (ord($_) & 0x7f) << (7 * $i++)  foreach (@bytes) ;
#    return $total ;
}


sub set_swf_u30_32 {
    my($val)= @_ ;
    return chr($val) if $val <= 0x7f ;    # shortcut for common case
    my $ret= reverse pack('w', $val) ;
    substr($ret, 0, 1)|= "\x80" ;
    substr($ret, -1, 1)&= "\x7f" ;
    return $ret ;
}


sub get_swf_u8 {
    my($in)= @_ ;
    $$in=~ /\G(.)/gcs ;
    return ord($1) ;
}

sub get_swf_s24 {
    my($in)= @_ ;
    $$in=~ /\G(.)(.)(.)/gcs ;
    my $val= ord($1) + (ord($2)<<8) + (ord($3)<<16) ;
    # Set sign if needed.
    $val= -(~$val & 0xffffff) - 1  if $val & 0x800000 ;
    return $val ;
}

sub set_swf_s24 {
    my($val)= @_ ;
    # Note that 'V' template is for unsigned, but pack() seems to accept
    #   negative input.
    return substr(pack('V', $val), 0, 3) ;
}


# Strings are in UTF-8 with preceding u30 size in bytes.
# In UTF-8, bytes not starting with "10" start a character, and bytes
#   starting with "10" are continuation bytes in the same character.
sub get_swf_string {
    my($in)= @_ ;
    my($size)= &get_swf_u30_32($in) ;
    my $ret= substr($$in, pos($$in), $size) ;
    pos($$in)+= $size ;
    return $ret ;
}

# One u30 count followed by u30[count] .
sub get_swf_ns_set {
    my($in)= @_ ;
    my $start_pos= pos($$in) ;
    my $count= &get_swf_u30_32($in) ;
    &skip_swf_u30_u32_s32($in)  foreach (1..$count) ;
    return substr($$in, $start_pos, pos($$in)-$start_pos) ;
}


# Format varies depending on first byte.
# We need to remember which ones use the name "connect", "play", "URLRequest",
#   "loaderURL", "loadPolicyFile", or "url".
#   in order to proxify elsewhere correctly.  For now, only worry about type 7
#   for this, since that's how those commands are compiled to bytecode.  A
#   malicious server could use a different type to get through this and learn
#   a user's IP address.
# This routine modifies $mn_specials in place.
sub get_swf_multiname {
    my($in, $mn_id, $n_specials, $mn_specials)= @_ ;
    my $start_pos= pos($$in) ;
    my($kind, $count) ;
    $$in=~ /\G(.)/gcs  && ($kind= ord($1)) ;
    if ($kind==0x07) {                         # QName
	&skip_swf_u30_u32_s32($in) ;
	my $name_id= &get_swf_u30_32($in) ;
	foreach my $p (qw(connect play URLRequest loaderURL loadPolicyFile url)) {
	    ($name_id==$_) && push(@{$mn_specials->{$p}}, $mn_id)  foreach (@{$n_specials->{$p}}) ;
	}
    } elsif ($kind==0x0d) {                    # QName, for attributes
	&skip_swf_u30_u32_s32($in) ;
	&skip_swf_u30_u32_s32($in) ;
    } elsif ($kind==0x0f or $kind==0x10) {     # RTQName
	&skip_swf_u30_u32_s32($in) ;
    } elsif ($kind==0x11 or $kind==0x12) {     # RTQNameL
    } elsif ($kind==0x13 or $kind==0x14) {     # NameL
    } elsif ($kind==0x09 or $kind==0x0e) {     # Multiname
	my $name_id= &get_swf_u30_32($in) ;
	&skip_swf_u30_u32_s32($in) ;
	foreach my $p (qw(connect play URLRequest loaderURL loadPolicyFile url)) {
	    ($name_id==$_) && push(@{$mn_specials->{$p}}, $mn_id)  foreach (@{$n_specials->{$p}}) ;
	}
    } elsif ($kind==0x1b or $kind==0x1c) {     # MultinameL
	&skip_swf_u30_u32_s32($in) ;
    } elsif ($kind==0x1d) {                    # ???
	&skip_swf_u30_u32_s32($in) ;
	$count= &get_swf_u30_32($in) ;
	&skip_swf_u30_u32_s32($in)  foreach (1..$count) ;
    }

    return substr($$in, $start_pos, pos($$in)-$start_pos) ;
}

sub get_swf_option_info {
    my($in)= @_ ;
    my $count= &get_swf_u30_32($in) ;
    for (1..$count) {           # option_detail
	&skip_swf_u30_u32_s32($in) ;
	pos($$in)++ ;
    }
}

sub get_swf_traits_info {
    my($in)= @_ ;
    my($kind, $flags, $vindex, $metadata_count) ;
    &skip_swf_u30_u32_s32($in) ;
    $$in=~ /\G(.)/gcs  && (($kind, $flags)= (ord($1) & 0x0f, ord($1)>>4)) ;
    if ($kind==0 or $kind==6) {     # Trait_Slot or Trait_Const
	&skip_swf_u30_u32_s32($in) ;
	&skip_swf_u30_u32_s32($in) ;
	$vindex= &get_swf_u30_32($in) ;
	pos($$in)++  if $vindex ;
    } elsif ($kind==4) {            # Trait_Class
	&skip_swf_u30_u32_s32($in) ;
	&skip_swf_u30_u32_s32($in) ;
    } elsif ($kind==5) {            # Trait_Function
	&skip_swf_u30_u32_s32($in) ;
	&skip_swf_u30_u32_s32($in) ;
    } elsif ($kind==1 or $kind==2 or $kind==3) {   # Trait_Method, Trait_Getter, or Trait_Setter
	&skip_swf_u30_u32_s32($in) ;
	&skip_swf_u30_u32_s32($in) ;
    }
    if ($flags & 0x04) {     # metadata
	$metadata_count= &get_swf_u30_32($in) ;
	&skip_swf_u30_u32_s32($in)  for (1..$metadata_count) ;
    }
}


sub get_swf_lookupswitch {
    my($in)= @_ ;
    my(@ret) ;
    push(@ret, &get_swf_s24($in)) ;
    my($count)= &get_swf_u30_32($in) ;
    push(@ret, $count) ;
    push(@ret, &get_swf_s24($in))  for (1..$count+1) ;

    return \@ret ;
}



#====================================================================



sub swf2perl {
    my($in)= @_ ;
    my($out) ;
    while ($in=~ /\G(.)/gcs) {
	my($chr)= $1 ;
	my($ord)= ord($chr) ;
	my($digit_follows) ;
	if ($in=~ /\G\d/gcs) {
	    $digit_follows= 1 ;
	    pos($in)-- ;
	}

	if ($ord==36 or $ord==64 or $ord==92 or $ord==34) {
	    $out.= "\\".chr($ord) ;
	} elsif ($ord>=32 and $ord<=126) {
	    $out.= chr($ord) ;
	} elsif ($ord>=1 and $ord<=26) {
	    $out.= "\\c".chr($ord+64) ;
	} elsif ($ord==0 and !$digit_follows) {
	    $out.= "\\0" ;
	} else {
	    $out.= "\\x".sprintf(($ord>255 ? "{%04x}" : "%02x"), $ord) ;
	}
    }
    return $out ;
}


#====================================================================


sub set_AVM2_BYTECODES {
    my $AVM2_hash= {
	"\xa0" => {name => 'add'},
	"\xc5" => {name => 'add_i'},
	"\x53" => {name => 'applytype',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x86" => {name => 'astype',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x87" => {name => 'astypelate'},
	"\xa8" => {name => 'bitand'},
	"\x97" => {name => 'bitnot'},
	"\xa9" => {name => 'bitor'},
	"\xaa" => {name => 'bitxor'},
	"\x41" => {name => 'call',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x43" => {name => 'callmethod',
		   params => [\&skip_swf_u30_u32_s32, \&skip_swf_u30_u32_s32]},
	"\x46" => {name => 'callproperty',
		   params => [\&get_swf_u30_32, \&get_swf_u30_32]},
	"\x4c" => {name => 'callproplex',
		   params => [\&skip_swf_u30_u32_s32, \&skip_swf_u30_u32_s32]},
	"\x4f" => {name => 'callpropvoid',
		   params => [\&get_swf_u30_32, \&get_swf_u30_32]},
	"\x44" => {name => 'callstatic',
		   params => [\&skip_swf_u30_u32_s32, \&skip_swf_u30_u32_s32]},
	"\x45" => {name => 'callsuper',
		   params => [\&get_swf_u30_32, \&get_swf_u30_32]},
	"\x4e" => {name => 'callsupervoid',
		   params => [\&get_swf_u30_32, \&get_swf_u30_32]},
	"\x78" => {name => 'checkfilter'},
	"\x80" => {name => 'coerce',
		   params => [\&get_swf_u30_32]},
	"\x82" => {name => 'coerce_a'},
	"\x85" => {name => 'coerce_s'},
	"\x42" => {name => 'construct',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x4a" => {name => 'constructprop',
		   params => [\&get_swf_u30_32, \&skip_swf_u30_u32_s32]},
	"\x49" => {name => 'constructsuper',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x76" => {name => 'convert_b'},
	"\x75" => {name => 'convert_d'},
	"\x73" => {name => 'convert_i'},
	"\x77" => {name => 'convert_o'},
	"\x70" => {name => 'convert_s'},
	"\x74" => {name => 'convert_u'},
	"\xef" => {name => 'debug',
		   params => [\&get_swf_u8, \&get_swf_u30_32, \&get_swf_u8, \&get_swf_u30_32]},
	"\xf1" => {name => 'debugfile',
		   params => [\&get_swf_u30_32]},
	"\xf0" => {name => 'debugline',
		   params => [\&get_swf_u30_32]},
	"\x94" => {name => 'declocal'},
	"\xc3" => {name => 'declocal_i'},
	"\x93" => {name => 'decrement'},
	"\xc1" => {name => 'decrement_i'},
	"\x6a" => {name => 'deleteproperty',
		   params => [\&skip_swf_u30_u32_s32]},
	"\xa3" => {name => 'divide'},
	"\x2a" => {name => 'dup'},
	"\x06" => {name => 'dxns',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x07" => {name => 'dxnslate'},
	"\xab" => {name => 'equals'},
	"\x72" => {name => 'esc_xattr'},
	"\x71" => {name => 'esc_xelem'},
	"\x5e" => {name => 'findproperty',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x5d" => {name => 'findpropstrict',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x59" => {name => 'getdescendants',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x64" => {name => 'getglobalscope'},
	"\x6e" => {name => 'getglobalslot',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x60" => {name => 'getlex',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x62" => {name => 'getlocal',
		   params => [\&skip_swf_u30_u32_s32]},
	"\xd0" => {name => 'getlocal_0'},
	"\xd1" => {name => 'getlocal_1'},
	"\xd2" => {name => 'getlocal_2'},
	"\xd3" => {name => 'getlocal_3'},
	"\x66" => {name => 'getproperty',
		   params => [\&get_swf_u30_32]},
	"\x65" => {name => 'getscopeobject',
		   params => [\&get_swf_u8]},
	"\x6c" => {name => 'getslot',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x04" => {name => 'getsuper',
		   params => [\&skip_swf_u30_u32_s32]},
	"\xb0" => {name => 'greaterequals'},         # note error in spec
	"\xaf" => {name => 'greaterthan'},
	"\x1f" => {name => 'hasnext'},
	"\x32" => {name => 'hasnext2',
		   params => [\&skip_swf_u30_u32_s32, \&skip_swf_u30_u32_s32]},   # just a guess... :P
	"\x13" => {name => 'ifeq',
		   params => [\&get_swf_s24]},
	"\x12" => {name => 'iffalse',
		   params => [\&get_swf_s24]},
	"\x18" => {name => 'ifge',
		   params => [\&get_swf_s24]},
	"\x17" => {name => 'ifgt',
		   params => [\&get_swf_s24]},
	"\x16" => {name => 'ifle',
		   params => [\&get_swf_s24]},
	"\x15" => {name => 'iflt',
		   params => [\&get_swf_s24]},
	"\x14" => {name => 'ifne',
		   params => [\&get_swf_s24]},
	"\x0f" => {name => 'ifnge',
		   params => [\&get_swf_s24]},
	"\x0e" => {name => 'ifngt',
		   params => [\&get_swf_s24]},
	"\x0d" => {name => 'ifnle',
		   params => [\&get_swf_s24]},
	"\x0c" => {name => 'ifnlt',
		   params => [\&get_swf_s24]},
	"\x19" => {name => 'ifstricteq',
		   params => [\&get_swf_s24]},
	"\x1a" => {name => 'ifstrictne',
		   params => [\&get_swf_s24]},
	"\x11" => {name => 'iftrue',
		   params => [\&get_swf_s24]},
	"\xb4" => {name => 'in'},
	"\x92" => {name => 'inclocal',
		   params => [\&skip_swf_u30_u32_s32]},
	"\xc2" => {name => 'inclocal_i',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x91" => {name => 'increment'},
	"\xc0" => {name => 'increment_i'},
	"\x68" => {name => 'initproperty',
		   params => [\&skip_swf_u30_u32_s32]},
	"\xb1" => {name => 'instanceof'},
	"\xb2" => {name => 'istype',
		   params => [\&skip_swf_u30_u32_s32]},
	"\xb3" => {name => 'istypelate'},
	"\x10" => {name => 'jump',
		   params => [\&get_swf_s24]},
	"\x08" => {name => 'kill',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x09" => {name => 'label'},
	"\xae" => {name => 'lessequals'},
	"\xad" => {name => 'lessthan'},
	"\x38" => {name => 'lf32'},
	"\x39" => {name => 'lf64'},
	"\x35" => {name => 'li8'},
	"\x36" => {name => 'li16'},
	"\x37" => {name => 'li32'},
	"\x1b" => {name => 'lookupswitch',
		   params => [\&get_swf_lookupswitch]},
	"\xa5" => {name => 'lshift'},
	"\xa4" => {name => 'modulo'},
	"\xa2" => {name => 'multiply'},
	"\xc7" => {name => 'multiply_i'},
	"\x90" => {name => 'negate'},
	"\xc4" => {name => 'negate_i'},
	"\x57" => {name => 'newactivation'},
	"\x56" => {name => 'newarray',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x5a" => {name => 'newcatch',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x58" => {name => 'newclass',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x40" => {name => 'newfunction',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x55" => {name => 'newobject',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x1e" => {name => 'nextname'},
	"\x23" => {name => 'nextvalue'},
	"\x02" => {name => 'nop'},
	"\x96" => {name => 'not'},
	"\x29" => {name => 'pop'},
	"\x1d" => {name => 'popscope'},
	"\x24" => {name => 'pushbyte',
		   params => [\&get_swf_u8]},
	"\x2f" => {name => 'pushdouble',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x27" => {name => 'pushfalse'},
	"\x2d" => {name => 'pushint',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x31" => {name => 'pushnamespace',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x28" => {name => 'pushnan'},
	"\x20" => {name => 'pushnull'},
	"\x30" => {name => 'pushscope'},
	"\x25" => {name => 'pushshort',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x2c" => {name => 'pushstring',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x26" => {name => 'pushtrue'},
	"\x2e" => {name => 'pushuint',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x21" => {name => 'pushundefined'},
	"\x1c" => {name => 'pushwith'},
	"\x48" => {name => 'returnvalue'},
	"\x47" => {name => 'returnvoid'},
	"\xa6" => {name => 'rshift'},
	"\x6f" => {name => 'setglobalslot',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x63" => {name => 'setlocal',
		   params => [\&skip_swf_u30_u32_s32]},
	"\xd4" => {name => 'setlocal_0'},
	"\xd5" => {name => 'setlocal_1'},
	"\xd6" => {name => 'setlocal_2'},
	"\xd7" => {name => 'setlocal_3'},
	"\x61" => {name => 'setproperty',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x6d" => {name => 'setslot',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x05" => {name => 'setsuper',
		   params => [\&skip_swf_u30_u32_s32]},
	"\x3d" => {name => 'sf32'},
	"\x3e" => {name => 'sf64'},
	"\x3a" => {name => 'si8'},
	"\x3b" => {name => 'si16'},
	"\x3c" => {name => 'si32'},
	"\xac" => {name => 'strictequals'},
	"\xa1" => {name => 'subtract'},
	"\xc6" => {name => 'subtract_i'},
	"\x2b" => {name => 'swap'},
	"\x50" => {name => 'sxi_1'},
	"\x51" => {name => 'sxi_8'},
	"\x52" => {name => 'sxi_16'},
	"\x03" => {name => 'throw'},
	"\x95" => {name => 'typeof'},
	"\xa7" => {name => 'urshift'},
    } ;

    @$AVM2_BYTECODES[map {ord} keys %$AVM2_hash]= (values %$AVM2_hash) ;
}


#----------------------------------------------------------------------
#  CPAN-related code
#----------------------------------------------------------------------

# Try to install CPAN modules.
sub install_modules {
    my(@modules)= @_ ;
    my($installed_local_lib, %env) ;
    
    my $needs_local_lib ;
    foreach (@modules) {
	eval "require $_" ;
	$needs_local_lib= 1, last  if $@ ;
    }

    require CPAN ;   # big module; don't require until needed
    require CPAN::FirstTime ;

    # local::lib lets us install modules under $HOME/perl5/ when we don't have
    #   root permissions.
    eval { require local::lib }  unless $>==0 ;
    
    if ($@ and $needs_local_lib) {
	# To bootstrap local::lib, we're supposed to use the manual command
	#   "perl Makefile.PL --bootstrap" when building.  Unfortunately, the
	#   CPAN module doesn't provide a way to pass a flag to that step of
	#   the process.  So here we emulate what happens in CPAN::FirstTime::init() ,
	#   which bootstraps the local::lib installation in the cpan utility.
	my $dist ;
	if ($dist= CPAN::Shell->expand('Module', 'local::lib')->distribution) {
	    $dist->{prefs}{pl}{commandline}= $LOCAL_LIB_DIR ne ''
		? "$^X Makefile.PL '--bootstrap=$LOCAL_LIB_DIR'"
		: "$^X Makefile.PL --bootstrap" ;
	    require lib ;
	    lib->import(CPAN::FirstTime::_local_lib_inc_path()) ;
	    eval { $dist->install } ;
	}
	if (!$dist or $@) {
	    die "Can't install local::lib: $@\n" ;
	} else {
	    require local::lib ;
	    $installed_local_lib= 1 ;
	    # Set environment variables, so subsequent installs work with local::lib .
	    # Next line is copied from CPAN::FirstTime::_local_lib_config(), except the
	    #   middle parameter of 0 has been added.  I think it's a bug in
	    #   CPAN::FirstTime::_local_lib_config(), as it disagrees with the code
	    #   in local::lib->build_environment_vars_for() .
	    my %env = local::lib->build_environment_vars_for(CPAN::FirstTime::_local_lib_path(), 0, 1) ;
	    @ENV{keys %env}= (values %env) ;
	}
    }

    # Clear these environment variables if root; otherwise, will install under
    #   user's $HOME.
    @ENV{qw(PERL_LOCAL_LIB_ROOT PERL_MB_OPT PERL_MM_OPT PERL5LIB)}= '' x 4  if $>==0 ;

    my @failed ;
    foreach (@modules) {
	my $rv= require_with_install($_) ;
	if    ($rv==2) { print "$_ installation succeeded\n" }
	elsif ($rv!=1) { print "FAILED: [$_] [$rv]\n" ; push(@failed, $_) }
    }
    print("Failed to install: [@failed]\n")  if @failed ;

    if ($installed_local_lib) {
	my $env= local::lib->environment_vars_string_for(CPAN::FirstTime::_local_lib_path()) ;
	if ($^O=~ /win/i) {
	    print <<EOI ;

*****************************************************************************
We had to install the module local::lib in order to install Perl modules
under your own directory rather than requiring administrator permissions to
install under the system directory.  To let CGIProxy find modules under your
own directory, please add these environment variables in your Control Panel's
System applet:

$env
EOI
	} else {
	    my $startup_file= $ENV{SHELL}=~ /csh/  ? '.cshrc'  : '.bashrc' ;
	    print <<EOI ;

*****************************************************************************
We had to install the module local::lib in order to install Perl modules
under your own directory rather than requiring root permissions to
install under the system directory.  To let CGIProxy find modules under your
own directory, these lines need to be added to $startup_file, in your home
directory:

$env
EOI
	    my $resp ;
	    do {
		print "Do you want them to be added for you right now? [y/n] " ;
		$resp= <> ;
		if ($resp=~ /^y/i) {
		    $startup_file= File::Spec->catfile(CPAN::FirstTime::_local_lib_home(), $startup_file) ;
		    open(STARTUP, '>>', $startup_file) or die "Can't open $startup_file: $!\n" ;
		    print STARTUP $env ;
		    close(STARTUP) ;
		}
	    } until $resp=~ /^[yn]/i ;
	}
	my $local_lib_dir= CPAN::FirstTime::_local_lib_path() ;
	print <<EOI ;
*****************************************************************************
IMPORTANT: Since we installed local::lib, you need to configure CGIProxy to
look in the directory it uses, by setting \$LOCAL_LIB_DIR='$local_lib_dir'
near the top of the script.
*****************************************************************************
EOI
    }
}


# Load a module, installing it if required.
# Returns 1 upon 'require' success, 2 upon success and installation, and undef on failure.
sub require_with_install {
    my($module, $die_on_failure)= @_ ;
    eval "require $module" ;
    return 1 unless $@ ;
    warn "Couldn't require $module, attempting install: $@\n" ;   # jsm-- see warnings, and handle normal cases here!
    require CPAN ;   # big module; don't require until needed
    CPAN::Shell->install($module) ;
    # install() doesn't always return true upon success, so test it.
    eval "require $module" ;
    if ($@) {
	return undef unless $die_on_failure ;
	&HTMLdie(<<EOM) ;
Couldn't install Perl's $module module.  Try installing it manually,
perhaps by running "cpan $module" from the command line.
EOM
    }
    return 2 unless $@ ;
    return undef unless $die_on_failure ;
    &HTMLdie("Seemed to install $module OK, but can't load it.") ;
}


#----------------------------------------------------------------------
#  Database-related code
#----------------------------------------------------------------------

sub create_database {
    my $dbh ;

    require_with_install('DBI', 1) ;
    $dbh= $DBH || DBI->connect("dbi:$DB_DRIVER:database=$DB_NAME", $DB_USER, $DB_PASS, { AutoCommit => 1 }) ;
    if (!$dbh) {   # jsm-- handle other common error cases!
	# No $DB_NAME database yet; try to connect to engine with no database requested.
	$dbh= DBI->connect("dbi:$DB_DRIVER:", $DB_USER, $DB_PASS, { AutoCommit => 1 })
	    or &HTMLdie("Can't connect to database engine: $DBI::errstr") ;
	defined $dbh->do("create database $DB_NAME ;")   # jsm-- but what if it's there already?
	    or &HTMLdie("Can't create database '$DB_NAME' (try doing it manually): $DBI::errstr") ;
	# Clobbering old $dbh makes it disconnect.
	$dbh= DBI->connect("dbi:$DB_DRIVER:database=$DB_NAME", $DB_USER, $DB_PASS, { AutoCommit => 1 })
	    or &HTMLdie("Can't connect to new '$DB_NAME' database: $DBI::errstr") ;
    }
    # Now $dbh has working handle to $DB_NAME database.

    # Not all database drivers can handle multiple statements, so do one at a time.
    # jsm-- for sites with heavy usage, may need to avoid DELETE CASCADE.
    my(@stmts)= split(/;/, <<EOS) ;
create table session (
  id varchar(64) NOT NULL,
  ip_address varchar(15) NOT NULL,
  last_used datetime NOT NULL,
  CONSTRAINT id PRIMARY KEY (id)
) ;
create index session_last_used on session (last_used) ;
create index session_ip_address on session (ip_address) ;

create table cookie (
  session varchar(64) NOT NULL,
  name varchar(4096),
  value varchar(4096),
  expires datetime,
  domain varchar(256),
  path varchar(1024),
  secure tinyint,
  httponly tinyint,
  CONSTRAINT session_con FOREIGN KEY(session)
    REFERENCES session(id)
    ON DELETE CASCADE
) ;
create index cookie_session_path_domain on cookie (session, path, domain) ;
create index cookie_expires on cookie (expires) ;
EOS
    /\S/ && !$dbh->do($_)
	&& &HTMLdie("Can't create database tables: $DBI::errstr")  for @stmts ;

}


# Store a cookie in the database, under session $session_id .
# Only create global database and statement handles as needed.
# Currently returns 1 upon success, dies otherwise.
sub store_cookie_in_db {
    my($name, $value, $expires_clause, $path, $domain, $secure_clause, $httponly_clause)= @_ ;

    my($expires)= $expires_clause=~ /^expires\s*=\s*([^;]*)/i ;
    my $secure= $secure_clause ne ''  ? 1  : 0 ;
    my $httponly= $httponly_clause ne ''  ? 1  : 0 ;

    # Convert $expires to "YYYY-MM-DD HH:MM:SS".
    if (defined $expires) {
	my @t= $expires=~ /^\w+,\s*(\d+)[ -](\w+)[ -](\d+)\s+(\d+):(\d+):(\d+)/ ;
	$t[1]= $UN_MONTH{lc($t[1])} ;
	$t[2]+= 2000 if length($t[2])==2 ;
	$expires= defined $t[5]
	    ? sprintf('%04s-%02s-%02s %02s:%02s:%02s', @t[2, 1, 0, 3, 4, 5])
	    : undef ;
    }

    # Try to update existing cookie.
    $STH_UPD_COOKIE||= $DBH->prepare('UPDATE cookie SET value=?, expires=?, secure=?, httponly=? '
				   . 'WHERE session=? AND name=? AND domain=? AND path=?') ;
    &HTMLdie("Can't prepare STH_UPD_COOKIE: $DBI::errstr") unless defined $STH_UPD_COOKIE ;
    my $rv= $STH_UPD_COOKIE->execute($value, $expires, $secure, $httponly,
				     defined $expires  ? $session_id_persistent  : $session_id,
				     $name, $domain, $path) ;
    return 1 if $rv==1 ;    # success

    # Cookie doesn't exist yet; try an INSERT.
    $STH_INS_COOKIE||= $DBH->prepare('INSERT INTO cookie (session, name, value, expires, domain, path, secure, httponly) '
				      . 'VALUES (?, ?, ?, ?, ?, ?, ?, ?)') ;
    &HTMLdie("Can't prepare STH_INS_COOKIE: $DBI::errstr") unless defined $STH_INS_COOKIE ;
    $rv= $STH_INS_COOKIE->execute(defined $expires  ? $session_id_persistent  : $session_id,
				  $name, $value, $expires, $domain, $path, $secure, $httponly) ;
    return 1 if $rv==1 ;    # success

    &HTMLdie("Can't store cookie in database: $DBI::errstr") ;
}


# Get matching cookies from the database.
# Returns "name1=value1;name2=value2;..." .
# If $for_js is set, then only return those cookies with httponly=0 .
sub get_cookies_from_db {
    my($path, $host, $port, $scheme, $for_js)= @_ ;

    if (!$STH_SEL_COOKIE) {
	if ($DB_DRIVER eq 'mysql') {
	    # MySQL doesn't (can't) support the standard "||" concatenation operator,
	    #   but provides CONCAT() .
	    $STH_SEL_COOKIE= $DBH->prepare(<<EOS) ;
SELECT name, value, httponly FROM cookie
WHERE (session=? OR session=?)
  AND (domain=? OR ? LIKE CONCAT("%", domain))
  AND ? LIKE CONCAT(path, "%")
  AND (expires>NOW() OR expires IS NULL)
  AND (?='https' OR secure=0)
ORDER BY LENGTH(path) DESC ;
EOS
	} elsif ($DB_DRIVER eq 'Oracle') {
	    $STH_SEL_COOKIE= $DBH->prepare(<<EOS) ;
SELECT name, value, httponly FROM cookie
WHERE (session=? OR session=?)
  AND (domain=? OR ? LIKE "%"||domain)
  AND ? LIKE path||"%"
  AND (expires>SYSDATE OR expires IS NULL)
  AND (?='https' OR secure=0)
ORDER BY LENGTH(path) DESC ;
EOS
	} else {
	    &HTMLdie("Sorry, can't support $DB_DRIVER database yet.") ;
	}
	&HTMLdie("Can't prepare STH_SEL_COOKIE: $DBH->errstr") unless defined $STH_SEL_COOKIE ;
    }

    # Grab all results and push into @cookie array, avoiding duplicates.
    my $rv= $STH_SEL_COOKIE->execute($session_id, $session_id_persistent, $host, $host, $path, $scheme) ;
    &HTMLdie("Can't STH_SEL_COOKIE->execute: $DBI::errstr")  unless defined $rv ;
    $rv= $STH_SEL_COOKIE->fetchall_arrayref ;
    @$rv= grep {!$_->[2]} @$rv  if $for_js ;   # exclude cookies where httponly=1
    my(@cookies, %done) ;
    !$done{$_->[0]} && (push(@cookies, "$_->[0]=$_->[1]"), $done{$_->[0]}++)  foreach @$rv ;
    return join(';', @cookies) ;
}


# Get all cookies for a user from the database, returning them in an array of
#   hashes.  This is used for cookie management.
sub get_all_cookies_from_db {
    connect_to_db()  if !$DBH ;

    if (!$STH_SEL_ALL_COOKIES) {
	if ($DB_DRIVER eq 'mysql') {
	    $STH_SEL_ALL_COOKIES= $DBH->prepare(<<EOS) ;
SELECT name, value, expires, domain, path, secure, httponly FROM cookie
WHERE (session=? OR session=?) AND (expires>NOW() OR expires IS NULL) ;
EOS
	} elsif ($DB_DRIVER eq 'Oracle') {
	    $STH_SEL_ALL_COOKIES= $DBH->prepare(<<EOS) ;
SELECT name, value, expires, domain, path, secure, httponly FROM cookie
WHERE (session=? OR session=?) AND (expires>SYSDATE OR expires IS NULL) ;
EOS
	} else {
	    &HTMLdie("Sorry, can't support $DB_DRIVER database yet.") ;
	}
	&HTMLdie("Can't prepare STH_SEL_ALL_COOKIES: $DBH->errstr") unless defined $STH_SEL_ALL_COOKIES ;
    }

    # Build @cookies from results.
    my $rv= $STH_SEL_ALL_COOKIES->execute($session_id, $session_id_persistent) ;
    $rv= $STH_SEL_ALL_COOKIES->fetchall_arrayref({}) ;
    return @$rv ;
}


sub delete_cookies_from_db {
    connect_to_db()  if !$DBH ;

    if (!$STH_DEL_COOKIE) {
	$STH_DEL_COOKIE= $DBH->prepare('DELETE FROM cookie WHERE (session=? OR session=?) AND domain=? AND path=? AND name=?;') ;
	&HTMLdie("Can't prepare STH_DEL_COOKIE: $DBH->errstr") unless defined $STH_DEL_COOKIE ;
    }

    foreach (@_) {
	# Each cookie in @_ is "domain;path;name".
	my $rv= $STH_DEL_COOKIE->execute($session_id, $session_id_persistent, split(/;/)) ;
	&HTMLdie("Can't delete cookie ($_): $DBI::errstr")  unless defined $rv ;
    }
}


# Insert or update the session record with the current time.
sub update_session_record {
    my($session_id)= @_ ;

    # Try to update existing record.
    if (!$STH_UPD_SESSION) {
	if ($DB_DRIVER eq 'mysql') {
	    $STH_UPD_SESSION= $DBH->prepare('UPDATE session SET last_used=NOW() WHERE id=?') ;
	} elsif ($DB_DRIVER eq 'Oracle') {
	    $STH_UPD_SESSION= $DBH->prepare('UPDATE session SET last_used=SYSDATE WHERE id=?') ;
	} else {
	    &HTMLdie("Sorry, can't support $DB_DRIVER database yet.") ;
	}
	&HTMLdie("Can't prepare STH_UPD_SESSION: $DBI::errstr") unless defined $STH_UPD_SESSION ;
    }
    my $rv= $STH_UPD_SESSION->execute($session_id) ;
    return 1 if $rv==1 ;    # success

    # Cookie doesn't exist yet; try an INSERT.
    if (!$STH_INS_SESSION) {
	if ($DB_DRIVER eq 'mysql') {
	    $STH_INS_SESSION= $DBH->prepare('INSERT INTO session (id, ip_address, last_used) VALUES (?, ?, NOW())') ;
	} elsif ($DB_DRIVER eq 'Oracle') {
	    $STH_INS_SESSION= $DBH->prepare('INSERT INTO session (id, ip_address, last_used) VALUES (?, ?, SYSDATE)') ;
	} else {
	    &HTMLdie("Sorry, can't support $DB_DRIVER database yet.") ;
	}
	&HTMLdie("Can't prepare STH_INS_SESSION: $DBI::errstr") unless defined $STH_INS_SESSION ;
    }
    $rv= $STH_INS_SESSION->execute($session_id, $ENV{REMOTE_ADDR}) ;
    return 1 if $rv==1 ;    # success

    &HTMLdie("Can't update session record: $DBI::errstr") ;
}


# Remove all expired records from the database.
# This should be run as a cron job.
sub purge_db {
    connect_to_db()  if !$DBH ;

    # First, purge sessions not used in the last hour (should we make time configurable?).
    if (!$STH_PURGE_SESSIONS) {
	if ($DB_DRIVER eq 'mysql') {
	    $STH_PURGE_SESSIONS= $DBH->prepare('DELETE FROM session WHERE last_used<TIMESTAMPADD(HOUR,-1,NOW());') ;
	} elsif ($DB_DRIVER eq 'Oracle') {
	    $STH_PURGE_SESSIONS= $DBH->prepare('DELETE FROM session WHERE last_used<SYSDATE-1/24;') ;
	} else {
	    &HTMLdie("Sorry, can't support $DB_DRIVER database yet.") ;
	}
	&HTMLdie("Can't prepare STH_PURGE_SESSIONS: $DBH->errstr") unless defined $STH_PURGE_SESSIONS ;
    }
    my $rv= $STH_PURGE_SESSIONS->execute() ;
    &HTMLdie("Can't purge sessions: $DBI::errstr")  unless defined $rv ;

    # Next, purge cookies that either a) have expired, or b) aren't associated
    #   with an existing session.
    if (!$STH_PURGE_COOKIES) {
	if ($DB_DRIVER eq 'mysql') {
	    $STH_PURGE_COOKIES= $DBH->prepare('DELETE FROM cookie WHERE expires<NOW();') ;   # jsm-- extend this!
	} elsif ($DB_DRIVER eq 'Oracle') {
	    $STH_PURGE_COOKIES= $DBH->prepare('DELETE FROM cookie WHERE expires<SYSDATE;') ; # ditto
	} else {
	    &HTMLdie("Sorry, can't support $DB_DRIVER database yet.") ;
	}
	&HTMLdie("Can't prepare STH_PURGE_COOKIES: $DBH->errstr") unless defined $STH_PURGE_COOKIES ;
    }
    $rv= $STH_PURGE_COOKIES->execute() ;
    &HTMLdie("Can't purge cookies: $DBI::errstr")  unless defined $rv ;
}




# Returns true iff IP address stored in database is same as that of current connection.
sub verify_ip_address {
    my($session_id)= @_ ;

    $STH_SEL_IP||= $DBH->prepare('SELECT ip_address FROM session WHERE id=?') ;
    &HTMLdie("Can't prepare STH_SEL_IP: $DBI::errstr") unless defined $STH_SEL_IP ;
    my $rv= $STH_SEL_IP->execute($session_id) ;
    my @rv= $STH_SEL_IP->fetchrow_array ;
    &HTMLdie("Can't STH_SEL_IP->fetchrow_array(): $DBI::errstr")  unless @rv ;
    return $rv[0] eq $ENV{REMOTE_ADDR} ;
}


# Connect to database if needed, possibly creating it, and set $DBH .
# Reuse $DBH if it exists instead of reconnecting.
sub connect_to_db {
    &HTMLdie("Sorry, can't support $DB_DRIVER database yet.")  unless $DB_DRIVER=~ /^(?:mysql|Oracle)$/ ;
    require_with_install('DBI', 1) ;
    $DBH||= DBI->connect("dbi:$DB_DRIVER:database=$DB_NAME", $DB_USER, $DB_PASS, { AutoCommit => 1 }) ;
    if (!$DBH) {
	create_database() ;
	$DBH= DBI->connect("dbi:$DB_DRIVER:database=$DB_NAME", $DB_USER, $DB_PASS, { AutoCommit => 1 }) ;
	&HTMLdie("Can't connect to database: $DBI::errstr")  unless defined $DBH ;
    }
}


