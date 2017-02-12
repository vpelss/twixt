#!C:/Perl64/bin/perl.exe -w -d

use strict;
use Socket;
use CGI::Cookie;
use JSON;
#use Email::Valid;

my %in;
my %cookies = CGI::Cookie->fetch;
my $SEND_MAIL = "/usr/lib/sendmail -t"; #example: $SEND_MAIL="/usr/lib/sendmail -t";
my $SMTP_SERVER=''; #$SMTP_SERVER="mail.emogic or $SEND_MAIL.com"; #can't use both  $SEND_MAIL and $SMTP_SERVER
my $FROM_MAIL = "Twixt Mailer vpelss\@emogic.com";
my $SUBJECT_MAIL = "Twixt Subject";
my $path_to_users = './users';
my $user_file_extension = '.cgi';
my $path_to_games = './games';
my $game_filename = 'game';
my $game_extension = '.txt';
my $chat_filename = 'messages';
my $chat_extension = '.txt';
my $json = JSON->new->allow_nonref;

my $username; #global so all routines can access after login has been verified
my $password;
my $game; #file number no extension
my $public_private;
my $logged_in;

eval { &main(); };     # Trap any fatal errors so the program hopefully
if ($@) { &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

sub main()
{
#my $ttt = $ENV{'Authorization'};
%in = &parse_form();
my $command = $in{'command'};
#cookies are read in check_login
#set global values if possible
if ( $in{'game'} )
    { $game = $in{'game'} }
else
    {
    if  ( $cookies{'game'} ) { $game = $cookies{'game'}->value; }
    }
if ( $in{'public_private'} )
    { $public_private = $in{'public_private'} }
else
    {
    if  ( $cookies{'public_private'} ) { $public_private = $cookies{'public_private'}->value; }
    }

if ( $command eq 'register' ) { &register(); }
if ( $command eq 'reset_password' ) { &reset_password(); }
if ( $command eq 'forgot_password' ) { &forgot_password(); }
if ( $command eq 'forgot_username' ) { &forgot_username(); }
$logged_in = &login(); #sets / gets $username + password if any
if ( $command eq 'login' ) { &check_login() }
if ( $logged_in != 1)
    {#every command after this needs us to be logged in
    &send_system_message("Fail: You need to login first.");
    }
if ( $command eq 'create_game' ) { &create_game(); }
if ( $command eq 'get_games' ) { &get_games(); }
if ( $command eq 'update_board' ) { &update_board(); }
if ( $command eq 'send_move' ) { &incomming_move(); }
if ( $command eq 'send_chat' ) { &incomming_chat(); }
if ( $command eq 'delete_game' ) { &delete_game(); }

&send_system_message("End of code. Nothing was done. Command: $command");
} #main done

sub incomming_chat()
{
#see if this is our game?
my $game_hash_ref = &read_game_data_hash();
if ( ( $game_hash_ref->{'user1'} ne $username ) and ( $game_hash_ref->{'user2'} ne $username ) )
        {
        &send_system_message( "You are not a player in this game.");
        }

my $chat_text = $in{'chat_text'};
$chat_text =~ s/[^\d\w\s]//g; #sanitize
my $dir = "$path_to_games/$public_private/$game";
my $file = "$dir/$chat_filename$chat_extension";
open FILE , ">>$file";
print FILE "$username: $chat_text\n";
close FILE;

$game_hash_ref->{'pass'} = 10; #10 means no output to js screen
my $message = $json->encode( $game_hash_ref );
send_output($message);
}

sub register()
    { #get data
    my $message;
    my $username = $in{'username'};
    $username =~ s/\s\W//; #no white space, only alpha numeric
    my $password = $in{'password'};
    $password =~ s/\s\W//; #no white space, only alpha numeric
    my $email = $in{'email'};
    if ( $username eq '' or $password eq '' or $email eq '' )
                {    #form submit error
               &send_system_message( "Blank fields are not allowed");
                }
     if ( ! &valid_email($email) )
        {
       &send_system_message( "Not a valid email." );
        }
     if ( ! -e "$path_to_users")
            {#create next directory
            mkdir "$path_to_users";
            }
      if (! -e "$path_to_users/$username$user_file_extension")
          { #file does not exist #create folder
          #mkdir "$path_to_users/$username" , 0666;
          open (FILE , ">$path_to_users/$username$user_file_extension");
          my $crypt = crypt ($in{'password'} , 'yum') ;
          print FILE "$crypt\n";
          print FILE "$email\n";
          close FILE;
          my $cookie_username = CGI::Cookie->new(-name    =>  'username',
                         -value   =>  "$username" );
          my $cookie_password = CGI::Cookie->new(-name    =>  'password',
                         -value   =>  "$password" );
          print "Set-Cookie: $cookie_username\n";
          print "Set-Cookie: $cookie_password\n";

         &send_system_message( "Account created for <font color='red'><b>$username</b></font>. Remember this username <font color='red'><b>$username</b></font>.");
        }
     else
          {
          &send_system_message("Username $username already exists");
          }

     }

sub reset_password()
    { #get data
    my $message;
     my $username = $in{'username'};
     $username =~ s/\s\W//; #no white space, only alpha numeric
     my $old_password = $in{'oldpassword'};
     my $new_password = $in{'newpassword'};
     $new_password =~ s/\s\W//; #no white space, only alpha numeric
     if ( $username eq '' or $old_password eq '' or $new_password eq '')
          { #form submit error
         &send_system_message("Blank fields are not allowed");
          }
     if (! -e "$path_to_users/$username$user_file_extension")
        { #file does not exist
        &send_system_message( "Username $username does not exists" );
        }
     else
          {
          my $crypt_old_password = crypt ($old_password , 'yum') ;
          open (FILE , "<$path_to_users/$username$user_file_extension");
          my @download = <FILE>;
          close FILE;
          chomp @download;
          my $passwordencrypted = $download[0];
          my $email = $download[1];
          if ($crypt_old_password eq $passwordencrypted)
               {
               #can change!!!
               open (FILE , ">$path_to_users/$username$user_file_extension");
               my $crypt_new_password = crypt ($new_password , 'yum') ;
               print FILE "$crypt_new_password\n";
               print FILE "$email\n";
               close FILE;
               &send_system_message( "Password changed for <font color=red><b>$username</b></font>." );
               }
          else
               {
               &send_system_message("Old Password incorrect.");
               }
          }
     }

sub forgot_password()
     { #get data
      my $message;
     my $username = $in{'username'};
     $username =~ s/\s\W//; #no white space, only alpha numeric
     if ( $username eq '')
          { #form submit error
          $message .= "Blank fields are not allowed";
          exit;
          }
     if (! -e "$path_to_users/$username$user_file_extension")
          { #file does not exist
          &send_system_message("Username $username does not exists");
          }
     else
          {
          my $new_password = rand(999999999);
          my $new_password_crypt = crypt ( $new_password  , 'yum') ;
          open (FILE , "<$path_to_users/$username$user_file_extension");
          my @download = <FILE>;
          close FILE;
          chomp @download;
          my $email = $download[1];
          open (FILE , ">$path_to_users/$username$user_file_extension");
          print FILE "$new_password_crypt\n";
          print FILE "$email\n";
          close FILE;
         if ( &valid_email($email) )
               {
               my $mail_message = "$username Your new password is $new_password.";
               my $result = &sendmail($FROM_MAIL, $SEND_MAIL, $email , $SMTP_SERVER, 'Your new Twixt password', $mail_message );
               if ( $result == 1 )
                    {
                    &send_system_message("Password changed for <font color=red><b>$username</b></font> and sent to <font color=red><b>$email</b></font>.");
                    }
               else
                    {
                     &send_system_message("Email error $result.");
                    }
               }
          else
               {
               &send_system_message("Email $email is not valid.");
               }
          }
     }

sub forgot_username()
     {
      my $message;
     my $usernames;
     my $email = $in{'email'};
     if ( ! &valid_email($email) )
        {
        &send_system_message("Email $email is not valid.");
        }
     opendir( DIR, $path_to_users );
     my @dir = readdir(DIR);
     close DIR;
     my $found = 0; #assume a failure
     for my $username (@dir)
          {
            if ( $username eq '.' or $username eq '..' ) {next}
          my $user_file = "$path_to_users/$username";
          open (FILE , "<$user_file");
          my @download = <FILE>;
          close FILE;
          chomp @download;
          #my $username = $dir;
          my $email_from_file = $download[1];
          if ( $email_from_file eq $email )
               { #username found
                #$usernames .= $username . ' ';
               my $mail_message = "Your username is $username";
               my $result = &sendmail($FROM_MAIL, $SEND_MAIL, $email, $SMTP_SERVER, 'Your Twixt username', $mail_message );
               if ( ! $result == 1 )
                    {
                    &send_system_message("Email error $result.");
                    }
               $found = 1;
               #break();
               }
          }
     if ( $found == 0 )
          {
          &send_system_message("No username was found for $email");
          }
    else
        {
        &send_system_message("Your usernames were sent to <font color=red><b>$email</b></font>.");
        }
     }

sub delete_game()
{
my $game_hash_ref =  &read_game_data_hash();
if ( $username ne $game_hash_ref->{'user1'} )
  {
  &send_system_message("Only the game creator can delete this game.");
  }
if ( $public_private eq 'private' )
  {
  $public_private = $username;
  }
my $dir = "$path_to_games/$public_private/$game";
my $rs = opendir( DIR, $dir );
my @dir = readdir(DIR);
close DIR;
foreach my $file ( @dir )
  {
  if ( $file eq '.' or $file eq '..' ) {next();}
  unlink "$dir/$file" or warn "Could not unlink $file: $!";
  }
$rs = rmdir($dir);
&send_system_message("Game deleted.");
}

sub create_game()
        {
        my $message;
        my $result;
        my $username = $cookies{'username'}->value;
        my $public_private = $in{'public_private'};
        my $timestamp = time();
        my $dir = "$path_to_games";
        if ( ! -e $dir) #create path_to_games if required
            {
            $result = mkdir $dir;
            if ( $result == 0 ) { $message .= "Directory creation error for $dir : $!"; &send_system_message($message); }
            }
        if ( $public_private eq 'public' )
            {
            $dir = "$dir/public";
             }
        else
            {
            $dir = "$dir/$username";
            }
        if ( ! -e $dir)
            {#create next directory
            $result = mkdir $dir;
            if ( $result == 0 ) { $message .= "Directory creation error for $dir : $!"; &send_system_message($message); }
            }
        $dir = "$dir/$timestamp";
        $result = mkdir $dir;
        if ( $result == 0 ) { $message .= "Directory creation error for $dir : $!"; &send_system_message($message); }

        #create message file
        open FILE , ">$dir/$chat_filename$chat_extension";
        close FILE;

        #create game file
        open FILE , ">$dir/$game_filename$game_extension";
        my $game_hash_ref;
        $game_hash_ref->{'game'} = $timestamp;
        #$game_hash_ref->{'public_private'} = $public_private;
        $game_hash_ref->{'user1'} = $username;
        $game_hash_ref->{'next_move'} = $username;
        $game_hash_ref->{'next_move_color'} = 'blue';
        $game_hash_ref->{'number_of_users'} = 1;
        $game_hash_ref->{'moves'} = {};

         #create points that belong to no one. corners
        $game_hash_ref->{'points'}->{"0_0"} = 'corner';
        $game_hash_ref->{'points'}->{"0_23"} = 'corner';
        $game_hash_ref->{'points'}->{"23_0"} = 'corner';
        $game_hash_ref->{'points'}->{"23_23"} = 'corner';

        $message = $json->encode( $game_hash_ref );
        print FILE $message;
        close FILE;

        &send_system_message("$public_private game $timestamp created ");
        }

sub get_games()
    {
    #return a json object {public:[] , private[]}
     my %games;
    &get_games_list("$path_to_games/public" , \%games , 'public');
    &get_games_list("$path_to_games/$username" , \%games , 'private');

    my $game_hash_ref->{'pass'} = 4; #4 games list
    $game_hash_ref->{'games'} = { %games };

    my $message = $json->encode( $game_hash_ref );
    send_output($message);
    }

sub get_games_list()
{
#input game directory
#output the list of directories (games) and (users) in hash_ref
# $game{#}{user1}= $game{#}{user2}=
my @games;
my $games_dir = $_[0];
my $hash_ref = $_[1]; # eg \$games{'public'}
my $type = $_[2]; #public / private
my $file_output;
my  $output;

opendir( DIR, "$games_dir" );
my @dir = readdir(DIR);
close DIR;
for my $file_name (@dir)
    {
    if ($file_name ne '.' and $file_name ne '..')
        {
        open (FILE , "<$games_dir/$file_name/$game_filename$game_extension");
        $file_output = <FILE>;
        $output = $json->decode( $file_output );
        close FILE;

        my $game = $output->{'game'};
        $hash_ref->{$type}{$game}{'user1'} = $output->{'user1'};
        $hash_ref->{$type}{$game}{'user2'} = $output->{'user2'};
        }
    }
}

sub update_board()
    {
    my $message;
    #get : next move username , all moves array , put in JSON and send
    #get game data
    my $game_hash_ref =  &read_game_data_hash();

    #check to see if you are in user list
    #if yes, continue if no, and one user add user to game and continue
    #if two users return a fail message {'message' : 'fail'}
    if ( (  $game_hash_ref->{'number_of_users'} == 1 ) and ( $game_hash_ref->{'user1'} ne $username ) and ( $game_hash_ref->{'user2'} ne $username ) )
        {
        #only one player, and we are not one
        #add us to game
        $game_hash_ref->{'number_of_users'} = 2;
        $game_hash_ref->{'user2'} = $username;
        $game_hash_ref->{'next_move_color'} = 'blue'; #initially assume that user1 has not moved
        #if next move != user1, next move = us!
        if ( $game_hash_ref->{'user1'} ne $game_hash_ref->{'next_move'} )
          {#if next move != user1, next move = us!
          $game_hash_ref->{'next_move'} = $game_hash_ref->{'user2'};
          $game_hash_ref->{'next_move_color'} = 'red';
          }
        #create points that belong exclusively to players. eg edges
        for (my $y = 0 ; $y < 24 ; $y++)
          {#owned by user1
          $game_hash_ref->{'points'}->{"0_$y"} = $game_hash_ref->{'user1'};
          $game_hash_ref->{'points'}->{"23_$y"} = $game_hash_ref->{'user1'};
          }
        for (my $x = 0 ; $x < 24 ; $x++)
          {#pegs owned by user2
          $game_hash_ref->{'points'}->{"$x\_0"} = $game_hash_ref->{'user2'};
          $game_hash_ref->{'points'}->{"$x\_23"} = $game_hash_ref->{'user2'};
          }

        &save_game_data_hash( $game_hash_ref );
        }

    my $chat_text = &read_chat_text_string();
    $game_hash_ref->{'chat_text'} = $chat_text;
    $game_hash_ref->{'pass'} = 2;
    $message = $json->encode( $game_hash_ref );
    &send_output($message);
    }

 sub incomming_move()
    {
    my $move_string = $in{'move'};
    $move_string =~ s/[^_0-9]//g; #sanitize moves
    my ( $x1 , $y1 , $x2 , $y2 ) = split ( /_/ ,  $move_string );
    #normalize input move. The point with the lowest x value goes first.
    #required for checking existing moves. otherwise going the other way fails and duplicates move
    #also helps with halving images and divs from 8 to 4. Only use East side
    if ( $x2 < $x1 )
      {# $x2 is less than $x1 so swap and fix $move_string
      $move_string = "$x2\_$y2\_$x1\_$y1";
      ( $x1 , $y1 , $x2 , $y2 ) = split ( /_/ ,  $move_string );
      }

    #get game data
    my $game_hash_ref = &read_game_data_hash();

    #see if this is our game?
    if ( ( $game_hash_ref->{'user1'} ne $username ) and ( $game_hash_ref->{'user2'} ne $username ) )
        {
        &send_system_message( "You are not a player in this game.");
        }
    if ( $game_hash_ref->{'number_of_users'} ne 2 )
      {
      &send_system_message( "Awaiting another player first." );
      }
    if ( exists  $game_hash_ref->{'moves'}->{ $move_string } )
        {#existing move
        &send_system_message( "Move already exists." );
        }
    if ( exists $game_hash_ref->{'points'}->{ "$x1\_$y1" } )
      {
      if ( $game_hash_ref->{'points'}->{ "$x1\_$y1" } ne $game_hash_ref->{'next_move'} )
        {
        &send_system_message( "One of the pegs belongs to the opponent" );
        }
      }
    if ( exists $game_hash_ref->{'points'}->{ "$x2\_$y2" } )
      {
      if ( $game_hash_ref->{'points'}->{ "$x2\_$y2" } ne $game_hash_ref->{'next_move'} )
        {
         &send_system_message( "One of the pegs belongs to the opponent" );
        }
      }
    my $delta_x = abs($x1 - $x2) ;
    my $delta_y = abs($y1 - $y2) ;
    my $h_squared = ($delta_x * $delta_x) + ($delta_y * $delta_y);
    if ( $h_squared != 5 )
        {#block any move that is not delta 1 and delta 2
         &send_system_message( "Move can only be delta 1 and delta 2" );
        }
    if ( $username ne $game_hash_ref->{'next_move'} )
        {#not your move yet
        &send_system_message( "Not your move dude." );
        }
    #check if we are crossing other player's move
    my $other_player_name;
    if ( $game_hash_ref->{'user1'} eq $username )
      {
      $other_player_name = $game_hash_ref->{'user2'};
      }
    else
      {
      $other_player_name = $game_hash_ref->{'user1'};
      }
    if ( exists $game_hash_ref->{'illegal_moves'}->{ $username }->{ $move_string } )
      {
      &send_system_message('This move crosses another players move');
      }

    #set $illegal_moves{x1_y1_x2_y2} = 1 after placing a move
    #$illegal_moves_offsets{slope} = @( (9 arrays of offset from p1 x1_y1_x2_y2) , ()        )
    my %illegal_moves_offsets;
    my $dx = $x1 - $x2;
    my $dy = $y1 - $y2;
    my $marker = "0_0_$dx\_$dy";
    #nne
    $illegal_moves_offsets{'0_0_-1_2'} = [ '-1_-1_1_0' , '0_-1_2_0' , '-1_-2_1_-1' , '0_-2_2_-1' , '-1_0_1_-1' , '0_-1_2_-2' , '0_-1_1_1' , '0_-2_1_0' , '0_-3_1_-1' ];
    #ene
    $illegal_moves_offsets{'0_0_-2_1'} = ['-1_-1_1_0','0_-1_2_0','1_-1_3_0','0_-1_1_1','0_-2_1_0','1_-1_2_1','1_-2_2_0','0_1_1_-1','1_0_2_-2'];
    #ese
    $illegal_moves_offsets{'0_0_-2_-1'} = ['-1_1_1_0','0_1_2_0','1_1_3_0','0_1_1_-1','0_2_1_0','1_1_2_-1','1_2_2_0','0_-1_1_1','1_0_2_2'];
    #sse
    $illegal_moves_offsets{'0_0_-1_-2'} = ['-1_0_1_1','0_1_2_2','-1_1_1_0','0_1_2_0','-1_2_1_1','0_2_2_1','0_1_1_-1','0_2_1_0','0_3_1_1'];
    foreach my $offset ( @{ $illegal_moves_offsets{$marker} } )
      {
      my ($offset_x1,$offset_y1,$offset_x2,$offset_y2) = split '_' , $offset;
      my $new_x1 = $x1 + $offset_x1;
      my $new_y1 = $y1 + $offset_y1;
      my $new_x2 = $x1 + $offset_x2;
      my $new_y2 = $y1 + $offset_y2;
      $game_hash_ref->{'illegal_moves'}->{ $other_player_name }->{"$new_x1\_$new_y1\_$new_x2\_$new_y2"} = 1;
      }

    #add move to move list and save
    #increase move count
    $game_hash_ref->{'move_count'} = $game_hash_ref->{'move_count'} + 1;
     #use a hash to store moves to avoid duplicates
    $game_hash_ref->{'moves'}->{ $move_string }->{'move_count'} = $game_hash_ref->{'move_count'};
    #set owner of move
    $game_hash_ref->{'moves'}->{ $move_string }->{'move_owner'} = $game_hash_ref->{'next_move'};
    #build point ownership
    $game_hash_ref->{'points'}->{"$x1\_$y1"} = $game_hash_ref->{'next_move'};
    $game_hash_ref->{'points'}->{"$x2\_$y2"} = $game_hash_ref->{'next_move'};
    #change next_move
    if ( $game_hash_ref->{'next_move'} eq $game_hash_ref->{'user1'} )
        {
        $game_hash_ref->{'next_move'} = $game_hash_ref->{'user2'};
        $game_hash_ref->{'next_move_color'} = 'red';
        }
    else
        {
        $game_hash_ref->{'next_move'} = $game_hash_ref->{'user1'};
        $game_hash_ref->{'next_move_color'} = 'blue';
        }

    &save_game_data_hash( $game_hash_ref ); #save all changes
    #send to client
    $game_hash_ref->{'pass'} = 3;
    my $message = $json->encode( $game_hash_ref );
    &send_output($message);
    }

sub read_chat_text_string()
{
my $filename = "$path_to_games/$public_private/$game/$chat_filename$chat_extension";
#does file exist
if ( ! -e $filename )
  {
  &send_system_message( "Game \"$public_private $game\" does not exist." );
  }
#get game data
open FILE , "<$filename";
my @file_output = <FILE>;
close FILE;
my $file_output = join( '' , @file_output );
return $file_output;
}

sub read_game_data_hash()
{
my $message;
my $output;
my $filename = "$path_to_games/$public_private/$game/$game_filename$game_extension";
#does file exist
if ( ! -e $filename )
  {
  &send_system_message( "Game \"$public_private $game\" does not exist." );
  }
#get game data
open FILE , "<$filename";
my $file_output = <FILE>;
my $game_hash_ref = $json->decode( $file_output );
close FILE;
return $game_hash_ref;
}

sub save_game_data_hash()
{
my $game_hash_ref = $_[0];
open FILE , ">$path_to_games/$public_private/$game/$game_filename$game_extension";
my $message = $json->encode( $game_hash_ref );
print FILE $message;
close FILE;
}

sub login()
{#the only time we return is if we logged in and we do it silently as we use this every time script is run
#return 1 on success and a text message on fail
$username = $in{'username'};
$username =~ s/\s\W//; #no white space, only alpha numeric
$password = $in{'password'};
$password =~ s/\s\W//; #no white space, only alpha numeric
if ( $username eq '' and $password eq '')
    {#maybe cookies
    if  ( $cookies{'username'} )
        {$username = $cookies{'username'}->value;}
    if  ( $cookies{'password'} )
        {$password = $cookies{'password'}->value;}
        }
if ( $username eq '' or $password eq '')
        {#form submit error
        return 0;
        }
my $user_file = "$path_to_users/$username$user_file_extension";
if ( ! -e $user_file  )
        {#file does not exist
        return 0;
        }
    else
          {
          my $crypt = crypt ($password , 'yum') ;
          open (FILE , "<$user_file");
          my @download = <FILE>;
          close FILE;
          chomp @download;
          my $passwordencrypted = $download[0];
          if ($crypt eq $passwordencrypted)
            {
            my $cookie_username = CGI::Cookie->new(-name    =>  'username',
                         -value   =>  "$username" );
            my $cookie_password = CGI::Cookie->new(-name    =>  'password',
                         -value   =>  "$password" );
             print "Set-Cookie: $cookie_username\n";
             print "Set-Cookie: $cookie_password\n";
            #print "Content-type: text/html\n\n";
           return 1; #the only time we return is if we logged in and we do it silently as we use this every time script is run
            }
          else
            {
            return 0;
            }
          }
}

sub check_login()
{#only to tell client if a first 'logon' was successful
if($logged_in == 1)
  {
  &send_system_message('Logged in.');
  }
else
  {
  &send_system_message('Login credentials failed or user does not exist.');
  }
}

sub send_output
{
my $message = $_[0];
#print "Status: 401\n";
#print "WWW-Authenticate: Basic\n";
print "Content-type: text/html\n\n";
print $message;
exit;
}

sub send_system_message()
{
my $game_hash_ref->{'pass'} = 1; #0=game data 1=system message 2=means no output
$game_hash_ref->{'message'} =  $_[0];
my $message = $json->encode( $game_hash_ref );
send_output($message);
}

sub parse_form
{
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

sub cgierr
{
# --------------------------------------------------------
# Displays any errors and prints out FORM and ENVIRONMENT
# information. Useful for debugging.

if (my $debug == 0) {
     print "Epic fail....";
     }

print "<PRE>\n\nCGI ERROR\n==========================================\n";
$_[0]      and print "Error Message       : $_[0]\n";
$0         and print "Script Location     : $0\n";
$]         and print "Perl Version        : $]\n";

    print "\nForm Variables\n-------------------------------------------\n";
    foreach my $key (sort keys %in)
            {
            my $space = " " x (20 - length($key));
            print "$key$space: $in{$key}\n";
            }

    print "\nEnvironment Variables\n-------------------------------------------\n";
    foreach my $env (sort keys %ENV)
            {
            my $space = " " x (20 - length($env));
            print "$env$space: $ENV{$env}\n";
            }
print "\n</PRE>";

exit -1;
};

sub valid_email
{
my $username = qr/[a-z0-9_+]([a-z0-9_+.]*[a-z0-9_+])?/;
my $domain   = qr/[a-z0-9.-]+/;
#my $regex = $email =~ /^$username\@$domain$/;

 my $testmail = $_[0];
  if ($testmail =~/ /)
   { return 0; }
  #if ( $testmail =~ /(@.*@)|(\.\.)|(@\.)|(\.@)|(^\.)/ ||
  #$testmail !~ /^.+\@(\[?)[a-zA-Z0-9\-\.]+\.([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/ )
  if ( $testmail !~ /^$username\@$domain$/ )
   { return 0; }
   else { return 1; }
}

sub send_mail()
{#error codes below for those who bother to check result codes <gr>
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
    print MAIL qq|Content-Type: text/html; charset="iso-8859-1"
   Content-Transfer-Encoding: quoted-printable
   |
   ;
    print MAIL "\n\n";
    #print MAIL 'Mime-Version: 1.0'."\n";
    #print MAIL 'content-type:' . "text/HTML\n\n"; # <----------------- put the double \n\n here
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
