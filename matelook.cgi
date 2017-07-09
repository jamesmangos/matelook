#!/usr/bin/perl -w
#note to markers: file handles are occassionally named after the function to avoid potential conflicts in naming

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use File::Path;
use POSIX;

sub main() {    
	# define some global variables
	$debug = 0;
	$users_dir = "dataset-medium";
	$success_colour = "lime";
	$posts_per_page=7;
	my $query = new CGI;

	print "Content-Type: text/html\n";

	if (defined $ENV{HTTP_COOKIE}){#if the cookie is defined
		my @cookies = split(';',$ENV{HTTP_COOKIE});
		my $login = "false";
		for $line (@cookies){
			if ($line =~ /login=(z[0-9]{7})/){
				$username=$1;
				$login = "true";
			}
		}
		if ($login eq "true"){		#user is logged in, handle this case
			if (defined param('newpost') && param('newpost') eq "" && param('file_upload') eq ""){
				print home_page("Couldn't create a new post, it had no content", "red");
			}
			elsif (defined param('newpost')){
				my $new_post = saved_newlines(sanitise("message=${\param('newpost')}"))."\n";
				$new_post .= "from=$username\n";
				$new_post .= "time=${\get_date()}\n";
				
				my $message = "";
				my $colour = "";

				#get folder number
				@folders = glob "$users_dir/$username/posts/*";
				$post_num = 0;
				#set post_num to the highest folder number + 1
				foreach $folder (@folders){
					$folder =~ s/$users_dir\/$username\/posts\///g;
					if (int($folder) >= $post_num){
						$post_num = int($folder) + 1;
					}
				}
				#create file, put data in file and create comments folder
				mkdir("$users_dir/$username/posts/$post_num", 0755);
				if (open(F, '>', "$users_dir/$username/posts/$post_num/post.txt")){#create a new file with $user_dir/$username/posts/$post_num/post.txt
					print F "$new_post";
					close F;
				}
				else{
					#print "<!-- couldn't open $users_dir/$username/posts/$post_num/post.txt-->\n";
				}
				mkdir("$users_dir/$username/posts/$post_num/comments",0755);#create a new folder $user_dir/$username/posts/$post_num/comments
				#put the uploaded file into a file
				my $file = param('file_upload') || "";
				if (defined $file && $file ne ""){
					#from https://www.sitepoint.com/uploading-files-cgi-perl-2/
					#NOTE: important, the file upload form must be multipart
					my $upload_filehandle = $query->upload('file_upload');
					#file is a photo
					if ($file =~ /\.jpg$/){
						open ( UPLOADFILE, ">$users_dir/$username/posts/$post_num/img.jpg" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}	
						close UPLOADFILE;
					}
					#file is a video
					elsif ($file =~ /\.mp4/){
						open ( UPLOADFILE, ">$users_dir/$username/posts/$post_num/vid.mp4" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}	
						close UPLOADFILE;
					}
					else{
						$message = "file upoads must be eith a .jpg or a .mp4. The post was still created. You can delete the post and try reuploading";
						$colour = "red";
					}
				}
				send_email_to_zid(param('newpost')); #notify anyone mentioned in the post
				
				if ($message eq ""){
					$message = "Successfully made a new post";
					$colour = $success_colour;
				}
				print home_page($message, $colour);
			}
			elsif (defined param('newcomment') && param('newcomment') eq "" && param('file_upload') eq ""){
				print home_page("Couldn't create a new comment, it had no content", "red");
			}
			elsif (defined param('newcomment')){
				#grab the folder the comment is goign in
				my $comment_folder = param('postid');
				#change the post file to reflect the latest editing date
				if (open(F, '<',$comment_folder)){
					my $string = "";
					foreach $line (<F>){
						chomp $line;
						next if $line =~ /^time=/;
						$string .= "$line\n";
					}
					$string .= "time=${\get_date()}\n";
					close F;
					if (open(F, '>',$comment_folder)){
						print F $string;
						close F;
					}
				}
				
				$comment_folder =~ s/\/post.txt//g;
				#create the message
				my $comment = saved_newlines(sanitise("message=${\param('newcomment')}\n"));
				$comment .= "from=$username\n";
				$comment .= "time=${\get_date()}\n";
				#get folder number
				@folders = glob "$comment_folder/comments/*";
				$folder_number = 0;
				#set post_num to the highest folder number + 1
				foreach $folder (@folders){
					$folder =~ s/$comment_folder\/comments\///g;
					if (int($folder) >= $folder_number){
						$folder_number  = int($folder) + 1;
					}
				}

				#create file, create folder
				mkdir("$comment_folder/comments/$folder_number", 0755);
				if (open(F, '>', "$comment_folder/comments/$folder_number/comment.txt")){#create a new file with $user_dir/$username/posts/$post_num/post.txt
					print F "$comment";
					close F;
				}
				else{
					#print "<!-- couldn't open $comment_folder/comments/$folder_number/comment.txt-->\n";
				}
				mkdir("$comment_folder/comments/$folder_number/replies",0755);#create a new folder $user_dir/$username/posts/$post_num/comments
				#put the uploaded file into a file
				my $file = param('file_upload') || "";
				if (defined $file && $file ne ""){
					#from https://www.sitepoint.com/uploading-files-cgi-perl-2/
					#NOTE: important, the file upload form must be multipart
					my $upload_filehandle = $query->upload('file_upload');
					#file is a photo
					if ($file =~ /\.jpg$/){
						open ( UPLOADFILE, ">$comment_folder/comments/$folder_number/img.jpg" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}	
						close UPLOADFILE;
					}
					#photo is a video
					elsif ($file =~ /\.mp4/){
						print "";
						open ( UPLOADFILE, ">$comment_folder/comments/$folder_number/vid.mp4" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}	
						close UPLOADFILE;
					}
				}
				send_email_to_zid(param('newcomment')); #notify anyone mentioned in the post

				print home_page("Successfully made a new comment","$success_colour");
			}
			elsif (defined param('newreply') && param('newreply') eq "" && param('file_upload') eq ""){
				print home_page("Couldn't create a new reply, it had no content", "red");
			}
			elsif (defined param('newreply')){
				#grab the folder the reply is goign in
				my $reply_folder = param('commentid');
				#change the post file to reflect the latest editing date
				my $post_file = $reply_folder;
				$post_file =~ s/comments\/.*\/comment.txt/post.txt/g;
				if (open(F, '<',$post_file)){
					my $string = "";
					foreach $line (<F>){
						chomp $line;
						next if $line =~ /^time=/;
						$string .= "$line\n";
					}
					$string .= "time=${\get_date()}\n";
					close F;
					if (open(F, '>', $post_file)){
						print F $string;
						close F;
					}
				}
			
				$reply_folder =~ s/\/comment.txt//g;
				#create the message
				my $reply = saved_newlines(sanitise("message=${\param('newreply')}\n"));
				$reply .= "from=$username\n";
				$reply .= "time=${\get_date()}\n";
				#get folder number
				@folders = glob "$reply_folder/replies/*";
				$folder_number = 0;
				#set post_num to the highest folder number + 1
				foreach $folder (@folders){
					$folder =~ s/$reply_folder\/replies\///g;
					if (int($folder) >= $folder_number){
						$folder_number  = int($folder) + 1;
					}
				}

				#create file, create folder
				mkdir("$reply_folder/replies/$folder_number", 0755);
				if (open(F, '>', "$reply_folder/replies/$folder_number/reply.txt")){#create a new file with $user_dir/$username/posts/$post_num/post.txt
					print F "$reply";
					close F;
				}
				else{
					#print "<!-- couldn't open $reply_folder/replies/$folder_number/reply.txt-->\n";
				}
				#put the uploaded file into a file
				my $file = param('file_upload') || "";
				if (defined $file && $file ne ""){
					#from https://www.sitepoint.com/uploading-files-cgi-perl-2/
					#NOTE: important, the file upload form must be multipart
					my $upload_filehandle = $query->upload('file_upload');
					#file is a photo
					if ($file =~ /\.jpg$/){
						open ( UPLOADFILE, ">$reply_folder/replies/$folder_number/img.jpg" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}	
						close UPLOADFILE;
					}
					#file is a video
					elsif ($file =~ /\.mp4/){
						print "";
						open ( UPLOADFILE, ">$reply_folder/replies/$folder_number/vid.mp4" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}	
						close UPLOADFILE;
					}
				}
				send_email_to_zid(param('newreply')); #notify anyone mentioned in the reply

				print home_page("Successfully made a new reply","$success_colour");
			}
			elsif (defined param('del_prof_img')){
				print page_header() if $debug;
				print "deleting profile image\n" if $debug;
				unlink "$users_dir/$username/profile.jpg";
				print edit_details_page();
			}
			elsif (defined param('del_back_img')){
				print page_header() if $debug;
				print "deleting background image\n" if $debug;
				unlink "$users_dir/$username/background.jpg";
				print edit_details_page();
			}
			elsif (defined param('delete')){#deleting a post, comment or reply
				#print page_header() if $debug;
				my $folderid = param('folderid');
				my $success = rmtree($folderid);
				print home_page();
				print "<!-- attempting to delete $folderid, it returned $success-->\n";
			}
			elsif (defined param('accept_decline')){ #handle friend request
				print page_header() if $debug;
				my $zid_to_mate = param('zid_to_mate');
				#remove from handle list
				if (open(F, '<', "$users_dir/$username/user.txt")){
					my $string = "";
					foreach $line (<F>){
						next if $line =~ /^mate_request_handle=/;
						$string .= $line;
					}
					close F;
					my @list = get_detail_list($username, "mate_request_handle");
					@list = remove_from_list(@list, $zid_to_mate);#remove from list $zid_to_mate
					$string .= "mate_request_handle=".reconstruct_list(@list)."\n";
					if (open(F, '>', "$users_dir/$username/user.txt")){
						print F $string;
						close F;
						print "<!-- users file after first write is $string-->\n" if $debug;
					}
					else{
						print "<!--couldn't write to self user.txt-->" if $debug;
					}
				}
				else{
					print "<!--couldn't readd from self user.txt-->" if $debug;
				}
				#remove other user from pending list
				if (open(F, '<', "$users_dir/$zid_to_mate/user.txt")){
					my $string = "";
					foreach $line (<F>){
						next if $line =~ /^pending_mate_requests=/;
						$string .= $line;
					}
					close F;
					my @list = get_detail_list($zid_to_mate, "pending_mate_requests");
					@list = remove_from_list(@list, $username);#remove from list $zid_to_mate
					$string .= "pending_mate_requests=".reconstruct_list(@list)."\n";
					if (open(F, '>', "$users_dir/$zid_to_mate/user.txt")){
						print F $string;
						close F;
						print "<!-- requesters user file after first write is $string-->\n" if $debug;
					}
					else{
						print "<!--couldn't write to other user.txt-->" if $debug;
					}
				}
				else{
					print "<!--couldn't readd from other user.txt-->" if $debug;
				}
				#if accept
				if (param('accept_decline') eq "Accept"){
					#add user to mate list
					if (open(F, '<', "$users_dir/$zid_to_mate/user.txt")){
						my $string = "";
						foreach $line (<F>){
							next if $line =~ /^mates=/;
							$string .= $line;
						}
						close F;
						my @list = get_detail_list($zid_to_mate, "mates");
						push @list, $username;
						$string .= "mates=".reconstruct_list(@list)."\n";
						if (open(F, '>', "$users_dir/$zid_to_mate/user.txt")){
							print F $string;
							close F;
							print "<!-- users file after second write is $string-->\n" if $debug;
						}
						else{
							print "<!--couldn't write to other user.txt-->" if $debug;
						}
					}
					else{
						print "<!--couldn't read from other user fle\n-->" if $debug;
					}
					#add other person to matelist
					if (open(F, '<', "$users_dir/$username/user.txt")){
						my $string = "";
						foreach $line (<F>){
							next if $line =~ /^mates=/;
							$string .= $line;
						}
						close F;
						my @list = get_detail_list($username, "mates");
						push @list, $zid_to_mate;
						$string .= "mates=".reconstruct_list(@list)."\n";
						if (open(F, '>', "$users_dir/$username/user.txt")){
							print F $string;
							close F;
							print "<!-- requesters user file after first write is $string-->\n" if $debug;
						}
						else{
							print "<!--couldn't write to selfuser.txt-->" if $debug;
						}
					}
					else{
						print "<!--couldn't read from selfuser fle\n-->" if $debug;
					}
					print user_page($zid_to_mate)#display their user page
				}
				#if decline, do nothing since we have already removed each other from the relevant lists
				else{
					print home_page();#display home page
				}
			}
			elsif (defined param('zid_to_mate')){#initiate a mate request by adding each other to relevant lists
				print page_header() if $debug;
				my $zid_to_mate = param('zid_to_mate');
				#send email to user to mate 
				if (open(F, "$users_dir/$zid_to_mate/user.txt")){#get email
					my $email = "";
					my $mate_request_email = "";
					for $line (<F>){
						if ($line =~ /^email=/){
							$line =~ s/^email=//;
							chomp $line;
							$line =~ s/\s+$//;
							$email = $line;					
						}
						elsif ($line =~ /^mate_request_email=/){
							chomp $line;
							$line =~ s/^mate_request_email=//g;
							$mate_request_email = $line;
						}
					}
					if ($email ne "" && $mate_request_email eq "true"){
						my $message = "${\replace_zid($username)} has sent a mate request to you. Follow this link while logged in to respond: ${\this_url()}?user_page=$username\n";
						`echo "$message" | mail -s "Matelook mate notification" $email`;
					}
				}
				
				#modify own user.txt to show that a request has been sent
				if (open(F, '<', "$users_dir/$username/user.txt")){
					my $string = "";
					foreach $line (<F>){
						next if $line =~ /^pending_mate_requests=/;
						$string .= $line;
					}
					close F;
					my @list = get_detail_list($username, "pending_mate_requests");
					if (in_list_variable($zid_to_mate, @list)){
						print "<!-- a mate request has already been sent to this user-->\n" if $debug;
					}
					else{
						push @list, $zid_to_mate;
						$string .= "pending_mate_requests=".reconstruct_list(@list)."\n";
						if (open(F, '>', "$users_dir/$username/user.txt")){
							print F $string;
							close F;
							print "<!-- the users txt file is now $string-->\n" if $debug;
							#modify their txt to show that a request has been sent
							if (open(F, '<', "$users_dir/$zid_to_mate/user.txt")){
								my $string = "";
								my @mates_list = ();
								foreach $line (<F>){
									next if $line =~ /^mate_request_handle=/;
									if ($line =~ /^mates=/){
										$line =~ s/mates=\[//g;
										$line =~ s/\]//g;
										@mates_list = split(',',$line);
										next;
									}
									$string .= $line;
								}
								close F;
								@list = get_detail_list($zid_to_mate, "mate_request_handle");
								if (in_list_variable($username, @list)){
									print "<!-- a mate request has already been sent to this user-->\n" if $debug;
								}
								else{
									#make sure you are not already in their list of mates
									if (in_list_variable($username, @mates_list)){
										print "<!-- you are already this person's mate-->\n" if $debug;
									}
									else{
										push @list, $username;
										$string .= "mate_request_handle=".reconstruct_list(@list)."\n";
										if (open(F, '>', "$users_dir/$zid_to_mate/user.txt")){
											print F $string;
											close F;
											#print "<!-- the users txt file is now $string-->\n" if $debug;
										}
										else{
											print "<!-- failed to mate $user_to_unmate due to failure to open their user details file when writing to file-->\n" if $debug;
										}
									}
								}
							}
							else{
								print "<!-- failed to open user details in mate_user-->\n" if $debug;
							}
						}
						else{
							print "<!-- failed to mate $user_to_unmate due to failure to open own user details file when writing to file-->\n" if $debug;
						}
					}
				}
				else{
					print "<!-- failed to open user details in mate_user-->\n" if $debug;
				}
				#show user page indicating a request has been sent
				print user_page($zid_to_mate);
			}
			elsif (defined param('unmate_user')){
				print page_header() if $debug;
				my $user_to_unmate = param('zid_to_unmate');
				if (open(F, '<', "$users_dir/$username/user.txt")){
					my $string = "";
					foreach $line (<F>){
						$string .= $line;
					}
					$string =~ s/, $user_to_unmate\]/\]/; #try removin this mate from the end of the list
					$string =~ s/$user_to_unmate,//; #try removing this mate from the start or middle of the list
					$string =~ s/\[$user_to_unmate\]/\[\]/; #try removing this mate when they are the only mate
					close F;
					if (open(F, '>', "$users_dir/$username/user.txt")){
						print F $string;
					}
					else{
						print "<!-- failed to unmate $user_to_unmate due to failure to open user details file when writing to file-->\n" if $debug;
					}
					close F;
					if (open(F, '<', "$users_dir/$user_to_unmate/user.txt")){
						$string = "";
						foreach $line (<F>){
							$string .= $line;
						}
						$string =~ s/, $username\]/\]/; #try removin this mate from the end of the list
						$string =~ s/ $username,//; #try removing this mate from the start or middle of the list
						$string =~ s/\[$username\]/\[\]/; #try removing this mate when they are the only mate
						close F;
						if (open(F, '>', "$users_dir/$user_to_unmate/user.txt")){
							print F $string;
						}
						else{
							print "<!-- failed to unmate $username due to failure to open their user details file when writing to file-->\n" if $debug;
						}
					}
					else{
						print "<!-- failed to unmate $user_to_unmate due to failure to open their user details file-->\n" if $debug;
					}
				}
				else{
					print "<!-- failed to unmate $user_to_unmate due to failure to open user details file-->\n" if $debug;
				}
				print user_page($user_to_unmate);
			}
			elsif (defined param('save')){
				my $full_name = sanitise(param('full_name'));
				my $program = sanitise(param('program'));
				my $profile_text = saved_newlines(sanitise(param('profile_text')));
				#my $profile_text = sanitise(param('profile_text'));
				my $home_suburb = sanitise(param('home_suburb'));
				my $birthday = param('date');
				my $courses = sanitise(param('courses'));
				my $password_update = sanitise(param('password_update')) if $debug;
				my $mate_request_email = param('mate_request_email') || "";
				my $mention_email = param('mention_email') || "";
				
				my $string = "full_name=$full_name\n";
				$string .= "program=$program\n";
				$string .= "home_suburb=$home_suburb\n";
				$string .= "courses=$courses\n";
				$string .= "password=$password_update\n" if $debug;
				$string .= "birthday=$birthday\n";
				$string .= "mention_email=$mention_email\n";	
				$string .= "mate_request_email=$mate_request_email\n";	
				$string .= "profile_text=$profile_text\n";
				
				my $debug_message = " profile text is $profile_text}\n";
				
				#public fields
				my @public_fields = ();
				push @public_fields, param('public_program') if param('public_program');
				push @public_fields, param('public_profile_text') if param('public_profile_text');
				push @public_fields, param('public_home_suburb') if param('public_home_suburb');
				push @public_fields, param('public_birthday') if param('public_birthday');
				push @public_fields, param('public_courses') if param('public_courses');
				push @public_fields, param('public_prof_img') if param('public_prof_img');
				push @public_fields, param('public_back_img') if param('public_back_img');
				push @public_fields, param('public_mates') if param('public_mates');
				push @public_fields, param('public_posts') if param('public_posts');
				$string .= "public_fields=";
				$string .= join(',',@public_fields);
				$string.= "\n";

				#get the unchanged lines
				if (open(my $p, "$users_dir/$username/user.txt")){
					while ($line = <$p>){
						chomp $line;
						if ($line =~ /^email=|^zid=|^mates=|^mate_request_handle=|^pending_mate_requests=/){#only get these fields
							$string .= "$line\n";
						}
						if ($line =~ /^password=/ && !$debug){
							$string .= "$line\n";
						}
					}
					close $p;
				}
				else{
					#print "<!-- could not open the details file-->\n";
				}			

				my $message = "";
				my $colour = "";
				#put the uploaded image into image.jpg # validation maybe?
				my $image = param('img_file') || "";
				if (defined $image && $image ne ""){
					if ($image =~ /\.jpg$/){
						#from https://www.sitepoint.com/uploading-files-cgi-perl-2/
						#NOTE: important, the file upload form must be multipart
						my $upload_filehandle = $query->upload('img_file');
						open ( UPLOADFILE, ">$users_dir/$username/profile.jpg" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}
						close UPLOADFILE;
					}
					else{
						$message .= "profile image must be a .jpg";
						$colour = "red";
					}
					
				}
				#put the uploaded background image into background.jpg # validation maybe?
				my $back_img = param('back_img') || "";
				if (defined $image && $back_img ne ""){
					if ($image =~ /\.jpg$/){
						#from https://www.sitepoint.com/uploading-files-cgi-perl-2/
						#NOTE: important, the file upload form must be multipart
						my $upload_filehandle = $query->upload('back_img');
						open ( UPLOADFILE, ">$users_dir/$username/background.jpg" ) or die;
						binmode UPLOADFILE;
						while ( <$upload_filehandle> ){
							print UPLOADFILE;
						}
						close UPLOADFILE;
					}
					else{
						$message .= "profile image must be a .jpg";
						$colour = "red";
					}
				}

				#put string into user.txt
				if (open(F, '>', "$users_dir/$username/user.txt")){
					print F "$string";
					close F;
				}
				else{
					#print "<!-- couldn't open $users_dir/$username/user.txt-->\n";
				}			

				$message = "Great, everything was updated successfully!!" if $colour eq "";
				$colour = $success_colour if $colour eq "";
				print user_page($username, $message, $colour);
				print "<!-- Finished the save function, public fields is @public_fields-->\n" if $debug;
				print "<!-- debug message is $debug_message-->\n" if $debug;
			}
			elsif (defined param('edit')){
				print edit_details_page();
			}
			elsif (defined param('user_page')){
				print user_page(param('user_page'));
			}
			elsif (defined param('matesearch')){
				print mate_search_page(sanitise(param('matesearch')));
			}
			elsif (defined param('postsearch')){
				print post_search_page(sanitise(param('postsearch')));
			}
			else{
				print home_page();
			}
		}
		else{ # if the user is not logged in, handle the login case
			if (defined param('newaccount')){
				my $zid = param('zid');
				my $new_password = sanitise(param('newpassword'));
				my $confirm_password = sanitise(param('confirmpassword'));
				my $email = sanitise(param('email'));

				#confrim zid is z[0-9]{7}
				if ($zid =~ /^z[0-9]{7}$/){
					#check zid is unique
					my @users = glob("$users_dir/*");
					my $is_unique = 1;
					for $user (@users){
						if ($user eq "$users_dir/$zid"){
							$is_unique = 0;
							last;
						}
					}
					if ($is_unique){
						if ($new_password ne ""){#check new password is non empty
							if ($new_password eq $confirm_password){#check passwords match
								if ($email ne ""){#check email exists (email regex checking is done via email input field so no need to do it here)
									$message = "go to ${\this_url()}?confirm_account=$zid to confirm your account";
									mkdir("$users_dir/$zid", 0755);
									mkdir("$users_dir/$zid/posts", 0755);
									if (open(F, '>', "$users_dir/$zid/user.txt")){
										print F "zid=$zid\n";
										print F "email=$email\n";
										print F "password=$new_password\n";
										print F "confirmed=no\n";
									}
									`echo "$message" | mail -s "Matelook account registration" $email`;
									print page_header();
									warningsToBrowser(1);
									print login_page('Great! an email has been sent to your account to confirm your registration!', "$success_colour");
									#print "sending the message: $message.\nTo: $email";
									
								}
								else{
									print page_header();
									warningsToBrowser(1);
									print login_page('must supply an email', "red");
								}
							}
							else{
								print page_header();
								warningsToBrowser(1);
								print login_page('password and confirm password do not match', "red");
							}
						}
						else{
							print page_header();
							warningsToBrowser(1);
							print login_page('you must supply a password', "red");
						}
					}
					else{
						print page_header();
						warningsToBrowser(1);
						print login_page('this zid is already being used', "red");
					}
				}
				else{
					print page_header();
					warningsToBrowser(1);
					print login_page('zid must be a z followed by 7 digits', "red");
				}
			}
			elsif (defined param('new_password')){ # underscore is important. some fields use newpassword. Final step with user input
				my $new_password = sanitise(param('new_password'));
				my $zid = sanitise(param('zid'));
				my $confirm_password = sanitise(param('confirm_password'));
				
				#check that the password has had a change request
				if (open(F, '<',"$users_dir/$zid/user.txt")){
					my $string = "";
					my $change_password = 0;
					while (my $line = <F>){
						if ($line =~ /^password_change=true/){
							$change_password = 1;
						}
						elsif ($line =~ /^password=/){
							next;#don't copy the password, it will be added back after this
						}
						else {
							$string .= $line;
						}
					}
					if ($change_password){
						if ($new_password eq $confirm_password){
							$string .= "password=$new_password\n";
							close F;
							if (open(F, '>', "$users_dir/$zid/user.txt")){
								print F $string;
								close F;
								print page_header();
								warningsToBrowser(1);
								print login_page('Great! your password has been changed', "$success_colour");
							}
						}
						else{
							print page_header();
							print "<span style=\"color: red\">Password and confirm password must match</span>";
							print "<form method=\"POST\">Enter you new password<input type=\"password\" name=\"new_password\">";
							print "Confirm password<input type=\"password\" name=\"confirm_password\">";
							print "<input type=\"submit\"><input type=\"hidden\" name=\"zid\" value=\"$zid\"></form>";
							print "<a href=\"/~z5109924/ass2/matelook.cgi\">Or go back to the login page</a>\n";
						}
					}
					else{
						print page_header();
						warningsToBrowser(1);
						print login_page('no password recovery was requested by this user', "red");
					}
				}
				else{
					print page_header();
					warningsToBrowser(1);
					print login_page('woops, there was a problem', "red");
					print "<!-- couldn't open user file for zid $zid-->" if $debug;
				}
			}
			elsif (defined param('password_change')){#prompt for new password
				my $zid = param('password_change');
				#check if the password has had a change request (to avoid malicious password changes
				if (open(F, '<',"$users_dir/$zid/user.txt")){
					my $change_password = "0";
					foreach $line (<F>){
						if ($line =~ /^password_change=true/){
							$change_passowrd = "1";
						}
					}
					if ($change_passowrd){
						print page_header();
						print "<form method=\"POST\">Enter you new password<input type=\"password\" name=\"new_password\">";
						print "Confirm password<input type=\"password\" name=\"confirm_password\">";
						print "<input type=\"submit\"><input type=\"hidden\" name=\"zid\" value=\"$zid\"></form>";
						print "<a href=\"/~z5109924/ass2/matelook.cgi\">Or go back to the login page</a>\n";
					}
					else{
						print page_header();
						warningsToBrowser(1);
						print login_page('no password recovery was requested by this user', "red");
					}
				}
				else{
					print page_header();
					warningsToBrowser(1);
					print login_page('woops, there was a problem', "red");
					print "<!-- couldn't open user file for zid $zid-->" if $debug;
				}
			}
			elsif (defined param('recovery_zid')){#send email to user
				print page_header();
				my $zid = param('recovery_zid');
				if ($zid =~ /^z[0-9]{7}$/){
					#check email belongs to a user
					my $zid_exists = 0;
					my @users = glob("$users_dir/*");
					for $user (@users){
						if ($user eq "$users_dir/$zid"){
							$zid_exists = 1;
							last;
						}
					}
					if ($zid_exists){
						#if it does then 
						#add passord_change = true to file
						if (open(F, '<',"$users_dir/$zid/user.txt")){
							#print " opening $users_dir/$zid/user.txt\n";
							my $email = "";
							my $string = "";
							#get the contents of the file
							foreach $line (<F>){
								$string .= $line;
								if ($line =~ /^email=/){
									$line =~ s/^email=//;
									chomp $line;
									$line =~ s/\s+$//g;
									$email = $line;
									last;
								}
							}
							$string .= "password_change=true\n";
							close F;
							if (open(F, '>', "$users_dir/$zid/user.txt")){
								print F $string;
							}
							if ($email ne ""){
								my $message = "Follow this link to reset your password: ${\this_url()}?password_change=$zid\n";
								print "An email has been sent to $email.<br>Follow the link in the email to change your password\n";
								`echo "$message" | mail -s "Matelook password reset" $email`;
							}
							else{
								print "<!-- problem getting the email from the zid file -->\n" if $debug;
							}
						}
						else{
							print "<!-- problem opening the zid details file in recovery zid -->\n" if $debug;
						}
					}
					else{
						print "<span style=\"color: red\">Sorry, couldn't find that zid</span>";
						print "<form method=\"POST\">Enter your zid to be sent a recovery email<input type=\"text\" name=\"recovery_zid\"><input type=\"submit\"></form>";
						print "<a href=\"/~z5109924/ass2/matelook.cgi\">Or go back to the login page</a>\n";
					}
				}	
				else{
					print "<span style=\"color: red\">You need to include a valid zid</span>";
					print "<form method=\"POST\">Enter your zid to be sent a recovery email<input type=\"text\" name=\"recovery_zid\"><input type=\"submit\"></form>";
					print "<a href=\"/~z5109924/ass2/matelook.cgi\">Or go back to the login page</a>\n";
				}
			}
			elsif (defined param('forgot_password')){#prompt for zid
				print page_header();
				print "<form method=\"POST\">Enter your zid to be sent a recovery email<input type=\"text\" name=\"recovery_zid\"><input type=\"submit\"></form>";
				print "<a href=\"/~z5109924/ass2/matelook.cgi\">Or go back to the login page</a>\n";
			}
			elsif (defined param('confirm_account')){
				my $zid = param('confirm_account');
				if (open(F, '<',"$users_dir/$zid/user.txt")){
					#get the contents of the file, except for the confirmed line
					my $string = "";
					foreach $line (<F>){
						next if $line =~ /^confirmed=/;
						$string .= $line;
					}
					close F;
					if (open(F, '>', "$users_dir/$zid/user.txt")){
						print F "$string";
					}
				}
				print page_header();
				warningsToBrowser(1);
				print login_page('Your account has been confirmed! Thanks for signing up', "$success_colour");
			}
			else{
				attempt_login();
			}
		}
	}
	else{
		attempt_login();
	}
	print page_trailer();
}

sub attempt_login {
	#attempt to log the user in
	$username = param('username') || '';
	$password = param('password') || '';
	if ($username && $password){
		if (open(LOGIN_ATTEMPT, "$users_dir/$username/user.txt")){
			for $line (<LOGIN_ATTEMPT>){
				chomp $line;
				if ($line =~ /^password=(.*)/){
					$correct_password = $1;
					if ($password eq $correct_password){#successful authentication
						print "Set-Cookie: login=$username;\n";
						print home_page();
						last;
					}
					else{
						print page_header();
						warningsToBrowser(1);
						print login_page('incorrect password', "red"); # print incorrect password
					}
				}
			}
			close LOGIN_ATTEMPT;
		}
		else{ # print "couldn't find user/user does not exist"
			print page_header();
			warningsToBrowser(1);
			print login_page('user does not exist', "red");
		}
	}
	elsif ($username){
		print page_header();
		warningsToBrowser(1);
		print login_page('a password must be supplied', "red");#print that no password was supplied
	}
	elsif ($password){
		print page_header();
		warningsToBrowser(1);
		print login_page('a username must be supplied', "red");#print that no username was supplied
	}
	else{ # else direct to login page
		print page_header();
		warningsToBrowser(1);
		print login_page();
	}
}

sub saved_newlines {
	my ($string) = @_;
	$string =~ s/\n/\\n/g;
	return $string;
}

sub undo_saved_newline {
	my ($string) = @_;
	$string =~ s/\\n/\n/g;
	return $string;
}

sub sanitise {
	my ($string) = @_;
	$string =~ s/</&lt;/g;
	$string =~ s/>/&gt;/g;
	return $string;
}

sub profile_text_tags {#generate safe tags only
	my ($string) = @_;
	$string =~ s/&lt;b&gt;(.*)&lt;\/b&gt;/<b>${1}<\/b>/g;
	$string =~ s/&lt;i&gt;(.*)&lt;\/i&gt;/<i>${1}<\/i>/g;
	$string =~ s/&lt;em&gt;(.*)&lt;\/em&gt;/<em>${1}<\/em>/g;
	$string =~ s/&lt;strong&gt;(.*)&lt;\/strong&gt;/<strong>${1}<\/strong>/g;
	$string =~ s/&lt;mark&gt;(.*)&lt;\/mark&gt;/<mark>${1}<\/mark>/g;
	$string =~ s/&lt;small&gt;(.*)&lt;\/small&gt;/<small>${1}<\/small>/g;
	$string =~ s/&lt;del&gt;(.*)&lt;\/del&gt;/<del>${1}<\/del>/g;
	$string =~ s/&lt;ins&gt;(.*)&lt;\/ins&gt;/<ins>${1}<\/ins>/g;
	$string =~ s/&lt;sub&gt;(.*)&lt;\/sub&gt;/<sub>${1}<\/sub>/g;
	$string =~ s/&lt;sup&gt;(.*)&lt;\/sup&gt;/<sup>${1}<\/sup>/g;
	return $string;
}

sub this_url {#modified from http://www.perlmonks.org/?node_id=1032912 to not include query string and also for typo. generates the current url
	my $page_url = 'http';
	if ($ENV{HTTPS} eq "on") {
	    $page_url .= "s";
	}
	$page_url .= "://";
	if ($ENV{SERVER_PORT} != "80") {
	    $page_url .= $ENV{SERVER_NAME}.":".$ENV{SERVER_PORT}.$ENV{REQUEST_URI};
	} else {
	    $page_url .= $ENV{SERVER_NAME}.$ENV{REQUEST_URI};
	}
	$page_url =~ s/\?.*$//;
	return $page_url;
}

sub send_email_to_zid {#sends emails to all zids in arguement if they consent to mention emails
	my ($string) = @_;
	for $zid ($string =~ /z[0-9]{7}/g){
		if (open(EMAIL_TO_ZID, "$users_dir/$zid/user.txt")){#get email
			my $email = "";
			my $mention_email = "";
			for $line (<EMAIL_TO_ZID>){
				if ($line =~ /^email=/){
					$line =~ s/^email=//;
					chomp $line;
					$line =~ s/\s+$//;
					$email = $line;			
				}
				if ($line =~ /^mention_email=/){
					chomp $line;
					$line =~ s/^mention_email=//g;
					$mention_email = $line;
				}
			}
			close EMAIL_TO_ZID;
			if ($email ne "" && $mention_email eq "true"){
				my $message = replace_zid("$username mentioned you in a post, $zid\n");
				`echo "$message" | mail -s "Matelook notification" $email`;
			}
		}
	}
}

sub get_detail_list {#return a list from a particular field in the zid's user.txt file
	my ($zid, $field) = @_;
	my @list = ();
	if (open(DETAIL_LIST, '<', "$users_dir/$zid/user.txt")){
		for $line (<DETAIL_LIST>){
			if ($line =~ /^$field=/){
				foreach $zid ($line =~ /z[0-9]{7}/g){
					push @list, $zid;
				}
			}
		}
		close DETAIL_LIST;
	}
	return @list;
}

sub reconstruct_list{#put a user.txt list back together, given a perl list arguement
	my (@list) = @_;
	my $string = "[";
	$string .= "$list[0]";
	foreach $elem (@list){
		next if $elem eq $list[0];
		$string .= ", $elem";
	}
	$string .= "]";
	return $string;
}

sub convert_newline {#change a newline to a break tag
	my ($string) = @_;
	$string =~ s/\\n/<br>/g;
	return $string;
}

sub zid_link { # for eavery zid in arguement, convert to the full name and include a link
	my ($string) = @_;
	foreach $id ($string =~ /(z[0-9]{7})/g){
		if (open ZID_LINK, "$users_dir/$id/user.txt"){
			my @lines = <ZID_LINK>;
			for $line (@lines){
				chomp $line;#remove new lines
				if ($line =~ /^full_name=/){
					$line =~ s/full_name=//;#remove everything before and including =
					$line = $id if $line eq ""; #don't change the full name to a blank, just use the zid
					$string =~ s/$id/<a href=?user_page=$id>$line<\/a>/g;#replace zid wih name
					last;	
				}
			}
			close ZID_LINK;
		}
		else{
			print "<!-- couldn't find $id -->\n" if $debug;
		}
	}
	return $string;
}

sub replace_zid{ # for every zid in arg, convert ot full name and don't include a link (not sure this is used at toime of submission)
	my ($string) = @_;
	foreach $id ($string =~ /(z[0-9]{7})/g){
		if (open REPLACE_ZID, "$users_dir/$id/user.txt"){
			my @lines = <REPLACE_ZID>;
			for $line (@lines){
				chomp $line;#remove new lines
				if ($line =~ /^full_name=/){
					$line =~ s/full_name=//;#remove everything before and including =
					$string =~ s/$id/$line/g if $line ne "";#replace zid wih name only if a name is given (avoids an empty name in the navbar which can mean a user can never chnage their name)
					last;	
				}
			}
			close REPLACE_ZID;
		}
		else{
			print "<!-- couldn't find $zid -->\n" if $debug;
		}
	}
	return $string;
}

sub get_pic { # return a string with clckable picture given a string which may contain zids
	my ($ids) = @_;
	my $string = "";
	foreach $id ($ids =~ /(z[0-9]{7})/g){
		my $image_file = "$users_dir/$id/profile.jpg"; # all dataset pictures are .jpg
		if (open my $pic, "$image_file"){
			$string .= "<a href=?user_page=$id>\n<img src=\"$image_file\" style=\"width:2em;height:2em;\">\n</a>\n";
			close $pic;
		}
		else{
			$string .= "&nbsp&nbsp";
		}
	}
	return $string;
}

sub get_date {#return a string formatted in the correct rfc 3339 variant
	($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime();
	my $string = sprintf("%04d-%02d-%02dT%02d:%02d:%02d+0000", $year+1900, $mon+1, $mday, $hour, $min, $sec);
	$wday = $yday; #superflous uses to remove warnings
	$wday = $isdst; #superflous uses to remove warnings
	return $string;
}

sub replace_links {#return links given an http address. assumes space delimiters
	my ($string) = @_;
	$string =~ s/(https?:\/\/[^\s]+)/<a href=$1>$1<\/a>/g;
	return $string;
}

sub mate_search_page {
	my ($search) = @_;
	print page_header();
	# Now tell CGI::Carp to embed any warning in HTML
	warningsToBrowser(1);
	my $string = "";
	print navbar();
	
	#search for the username
	@users = sort(glob("$users_dir/*"));
	my @results = ();
	foreach $zid (@users){
		next if $zid eq "$users_dir/$username";
		my $details_filename = "$zid/user.txt";
		open my $p, "$details_filename" or die "can not open $details_filename: $!";
		while ($line = <$p>){
			chomp $line;
			if ($line =~ /^full_name=/ && $line =~ /$search/){
				push @results, $zid;
				last;
			}
		}
		close $p;
	}
	#show a list of clickable pictures and names 
	$string .= "<br>MateSearch results for: $search<br>\n<p>\n";
	
	@results = sort @results;#sor the results so that results are consistant
	print "<!-- @results -->\n" if $debug;
	
	#calculate page range
	my $pages = int(@results/$posts_per_page + 0.99);#ceil function
	my $page = param('page') || 1;
	$page--;#change the number to be zero indexed rather than 1 indexed
	my $min = $posts_per_page*$page;
	my $max = $min;	
	if ($#results < $posts_per_page*($page+1)-1){
		$max = $#results;
	}
	else{
		$max = $posts_per_page*($page+1)-1;
	}
	#siplay users
	foreach $zid (@results[$min..$max]){
		$zid =~ s/$users_dir\///g;
		next if $zid eq $username;#don't include self in matesearch results
		$string .= get_pic($zid);#print profile pic
		$string .= "<a href=?user_page=$zid>\n";
		$string .= replace_zid($zid);#print mate name
		$string .= "\n</a>\n<br>\n";
	}
	$string .= "<!-- min was $min and max was $max. Total posts is $#results , number of pages is hence $pages. page is $page-->\n" if $debug;	
	#display page selection
	$string .=  "<div class=\"pagination\">\n";
	foreach $i (1..$pages){
		if ($i == $page+1){
			$string .=  "<a href=\"?matesearch=$search&page=$i\"><b>$i</b><\/a>&nbsp;\n";
			next;
		}
		$string .=  "<a href=\"?matesearch=$search&page=$i\">$i<\/a>&nbsp;\n";
	}
	$string .=  "<\/div>\n";
	
	return $string;
}

sub sort_posts {
	my (@unsorted) = @_;
	#get the dates and put them in a hash with value = name and key = date
	my %hash;
	foreach $post (@unsorted){
		if(open(F, "$post")){
			foreach my $line (<F>){
				if ($line =~ /^time=/){
					$line =~ s/^time=//;
					$hash{$line} = $post;
					last;
				}
			}
		}
		else{
			print "<!-- failed to open $post in sort posts -->\n" if $debug;
		}
	}
	#get an array of the sorted keys
	my @keys = sort keys %hash;
	#create the sorted array using the sorted keys
	my @sorted = ();
	foreach $key (@keys){
		unshift @sorted, $hash{$key};
	}
	#print "<!-- sort posts returned @sorted-->\n" if $debug;
	return @sorted;
}

sub display_posts {
	my (@posts) = @_; #used ot store the list of posts to display
	my $posts = ""; #used to store the display output
	foreach $post_filename (@posts) { # foreach post
		if (open F, "$post_filename"){
			#store this post in a seperate variable in case the message is empty. Don't display empty posts
			my $this_post = "<div class=\"post\">\n";
			$this_post .= "<!-- $post_filename-->\n" if $debug;
			my $has_content = 0;
			my $message = "";
			my $from = "";
			my $time = "";
			foreach $line (<F>){
				chomp $line;
				if ($line =~ /^message=/){
					$line =~ s/^message=//g;
					$message = replace_links(zid_link(convert_newline($line)));
					$has_content = 1 if $line ne "";
				}
				if ($line =~ /^from/){
					$line =~ s/^from=//g;
					$from = $line;
				}
				if ($line =~ /^time=/){
					$line =~ s/^time=//;
					$time = $line;
				}
			}
			close F;
			#get image filename
			my $img_filename = $post_filename;
			$img_filename =~ s/post\.txt/img.jpg/;
			my $vid_filename = $post_filename;
			$vid_filename =~ s/post\.txt/vid.mp4/;
			my $has_img = 0;
			my $has_vid = 0;
			if (open(IMG, "$img_filename")){
					$has_img=1;
					$has_content=1;
					close IMG;
			}
			if (open(VID, "$vid_filename")){
					$has_vid=1;
					$has_content=1;
					close VID;
			}
			if (!$has_content){
				print "<!-- skipping $post_filename, it has no content-->\n" if $debug;
				next;
			}
			#add the actual message, don't include time when not debugging
			if ($debug){
				$this_post .= "<br><a href=?user_page=$from>${\replace_zid($from)}</a> said at $time:<br>$message\n";
			}
			else{
				$this_post .= "<br><a href=?user_page=$from>${\replace_zid($from)}</a> said:<br>$message\n";
			}
			$this_post .= "<br><img src=\"$img_filename\"  style=\"width:304px;height:228px;\">\n" if $has_img;
			$this_post .= "<br><video width=\"400\" controls><source src=\"$vid_filename\" type=\"video/mp4\"></video>\n" if $has_vid;
			
			#print delete button if the viewer was the poster
			if ($username eq $from){
				my $folder_to_delete = $post_filename;
				$folder_to_delete =~ s/\/post\.txt//;
				$this_post .= "<form method=\"POST\"><input type=\"submit\" name=\"delete\" value=\"Delete\" class=\"matelook_button\">";
				$this_post .= "<input type=\"hidden\" name=\"folderid\" value=\"$folder_to_delete\"></form>";
			}

			#print comment box
			$this_post .= "<div class=\"comment_input\" align=\"right\" enctype=\"multipart/form-data\">\n";
			$this_post .= "<form method=\"POST\" enctype=\"multipart/form-data\">";
			$this_post .= "<input type=\"text\" name=\"newcomment\">";
			$this_post .= "<input type=\"file\" name=\"file_upload\">\n";
			$this_post .= "<input type=\"submit\" value=\"Comment\" class=\"matelook_button\">";
			$this_post .= "<input type=\"hidden\" name=\"postid\" value=\"$post_filename\">";
			$this_post .= "</form>";
			$this_post .= "</div>";
			$this_post .= "<br>";

			#grab comments #z3275760/posts/1/comments/0/replies/0
			my $folder = $post_filename;
			$folder =~ s/\/post\.txt//g;
			my @comments = glob "$folder/comments/*/comment.txt"; # get all comment files
			#my @sorted_comments = sort {$a =~ m/\/\d+\// <=> $b =~ m/\/\d+\//} @comments; #sort comments
			my @sorted_comments = sort_posts(@comments);
			foreach $comment_filename (@sorted_comments){ # foreach comment
				if (open F, "$comment_filename"){
					my $has_content = 0;
					my $this_comment = "<div class=\"comment\">\n";
					my @content = ();
					foreach $line (<F>){
						chomp $line;
						if ($line =~ /^message=/){
							$line =~ s/^message=//g;
							$message = replace_links(zid_link(convert_newline($line)));
							$has_content = 1 if $line ne "";
						}
						if ($line =~ /^from/){
							$line =~ s/^from=//g;
							$from = $line;
						}
						if ($line =~ /^time=/){
							$line =~ s/^time=//;
							$time = $line;
						}
					}
					close F;
					#get image filename
					my $img_filename = $comment_filename;
					$img_filename =~ s/comment\.txt/img.jpg/;
					my $vid_filename = $comment_filename;
					$vid_filename =~ s/comment\.txt/vid.mp4/;
					my $has_img = 0;
					my $has_vid = 0;
					if (open(IMG, "$img_filename")){
							$has_img=1;
							$has_content=1;
							close IMG;
					}
					if (open(VID, "$vid_filename")){
							$has_vid=1;
							$has_content=1;
							close VID;
					}
					if (!$has_content){
						print "<!-- skipping $comment_filename, it has no content-->\n" if $debug;
						next;
					}
					#add the actual message, don't include time when not debugging
					if ($debug){
						$this_comment .= "<br><a href=?user_page=$from>${\replace_zid($from)}</a> said at $time:<br>$message\n";
					}
					else{
						$this_comment .= "<br><a href=?user_page=$from>${\replace_zid($from)}</a> said:<br>$message\n";
					}
					$this_comment .= "<br><img src=\"$img_filename\"  style=\"width:304px;height:228px;\">\n" if $has_img;
					$this_comment .= "<br><video width=\"400\" controls><source src=\"$vid_filename\" type=\"video/mp4\"></video>\n" if $has_vid;
					
					#print delete button if the viewer was the poster
					if ($username eq $from){
						my $folder_to_delete = $comment_filename;
						$folder_to_delete =~ s/\/comment\.txt//;
						$this_comment .= "<form method=\"POST\"><input type=\"submit\" name=\"delete\" value=\"Delete\" class=\"matelook_button\">";
						$this_comment .= "<input type=\"hidden\" name=\"folderid\" value=\"$folder_to_delete\"></form>";
					}

					#print reply box
					$this_comment .= "<div class=\"comment_input\" align=\"right\">\n";
					$this_comment .= "<form method=\"POST\" enctype=\"multipart/form-data\">";
					$this_comment .= "<input type=\"text\" name=\"newreply\">";
					$this_comment .= "<input type=\"file\" name=\"file_upload\">\n";
					$this_comment .= "<input type=\"submit\" value=\"Reply\" class=\"matelook_button\">";
					$this_comment .= "<input type=\"hidden\" name=\"commentid\" value=\"$comment_filename\">";
					$this_comment .= "</form>";
					$this_comment .= "</div>";
					#grab replies
					my $reply_folder = $comment_filename;
					$reply_folder =~ s/\/comment\.txt//g;
					my @replies = glob "$reply_folder/replies/*/reply.txt"; # get all reply files
					#my @sorted_replies = sort {$a =~ m/\/\d+\// <=> $b =~ m/\/\d+\//} @replies; #sort replies
					my @sorted_replies = sort_posts(@replies);
					foreach $reply_filename (@sorted_replies){
						if (open F, "$reply_filename"){
							my $has_content = 0;
							my $this_reply = "<div class=\"reply\">\n";
							my @content = ();
							foreach $line (<F>){
								chomp $line;
								if ($line =~ /^message=/){
									$line =~ s/^message=//g;
									$message = replace_links(zid_link(convert_newline($line)));
									$has_content = 1 if $line ne "";
								}
								if ($line =~ /^from/){
									$line =~ s/^from=//g;
									$from = $line;
								}
								if ($line =~ /^time=/){
									$line =~ s/^time=//;
									$time = $line;
								}
							}
							close F;
							#get image filename
							my $img_filename = $reply_filename;
							$img_filename =~ s/reply\.txt/img.jpg/;
							my $vid_filename = $reply_filename;
							$vid_filename =~ s/reply\.txt/vid.mp4/;
							my $has_img = 0;
							my $has_vid = 0;
							if (open(IMG, "$img_filename")){
									$has_img=1;
									$has_content=1;
									close IMG;
							}
							if (open(VID, "$vid_filename")){
									$has_vid=1;
									$has_content=1;
									close VID;
							}
							if (!$has_content){
								print "<!-- skipping $reply_filename, it has no content-->\n" if $debug;
								next;
							}
							#add the actual message, don't include time when not debugging
							if ($debug){
								$this_reply .= "<br><a href=?user_page=$from>${\replace_zid($from)}</a> said at $time:<br>$message\n";
							}
							else{
								$this_reply .= "<br><a href=?user_page=$from>${\replace_zid($from)}</a> said:<br>$message\n";
							}
							$this_reply .= "<br><img src=\"$img_filename\"  style=\"width:304px;height:228px;\">\n" if $has_img;
							$this_reply .= "<br><video width=\"400\" controls><source src=\"$vid_filename\" type=\"video/mp4\"></video>\n" if $has_vid;
							
							#print delete button if the viewer was the poster
							if ($username eq $from){
								my $folder_to_delete = $reply_filename;
								$folder_to_delete =~ s/\/reply\.txt//;
								$this_reply .= "<form method=\"POST\"><input type=\"submit\" name=\"delete\" value=\"Delete\" class=\"matelook_button\">";
								$this_reply .= "<input type=\"hidden\" name=\"folderid\" value=\"$folder_to_delete\"></form>";
							}

							$this_reply .= "</div>\n";
							$this_comment .= $this_reply;
						}
					}
					$this_comment .= "</div>\n";#end comment
					$this_post .= $this_comment;
				}
				else{
					print "<!-- failed to open $comment_filename-->" if $debug;
				}
			}
			$this_post .= "</div><br>\n";#end post
			$posts .= $this_post;
		}
		else{
			print "<!-- couldn't open $post_filename in display posts-->\n" if $debug;
		}
    }
	return $posts;
}

sub home_page {
	my ($message, $colour) = @_;
	print page_header();
	warningsToBrowser(1);

	print navbar();
	if (defined $message && $message ne ""){
		print "<span style=\"color: $colour\">$message</span>\n";
	}
	print new_post_box();

	#get all posts
	my @all_posts = glob("$users_dir/*/posts/*"); #for all posts
	#put into a hash
	foreach $post (@all_posts){
		$posts_hash{$post} = 1;
	}
	#get user posts
	@self_posts = glob("$users_dir/$username/posts/*/post\.txt");#get posts by the user
	my @posts_to_display = @self_posts;
	#remove user posts from hash
	foreach $post (@self_posts){
		$post =~ s/\/post\.txt$//g;#remove the final level, all posts is folders, self is txts
		$posts_hash{$post} = 0;
	}
	#get list of mates
	my @mate_list = ();
	my $details_filename = "$users_dir/$username/user.txt";
	open my $p, "$details_filename" or die "can not open $details_filename: $!";
	while (my $line = <$p>){
		chomp $line;
		if ($line =~ /^mates=\[(.*)\]/){
			@mate_list = split(',',$1);
			last;
		}
	}
	close $p;
	#get list of mates posts
	my @mates_posts = ();
	foreach $mate (@mate_list){
		my @this_mates_posts = glob("$users_dir/$mate/posts/*/post\.txt");
		push @mates_posts, @this_mates_posts;
	}
	#push to final list
	push @posts_to_display, @mates_posts;
	#remove mates posts from hash 
	foreach $post (@mates_posts){
		$post =~ s/\/post\.txt$//g;#remove the final level, all posts is folders, self is txts
		$posts_hash{$post} = 0;
	}
	#search remaining posts for search terms
	foreach $key (keys %posts_hash){
		push @posts_to_search, $key if $posts_hash{$key};
	}
	my @results = post_search($username, @posts_to_search);
	push @posts_to_display, @results;

	#remove things that aren't post.txt
	my @tmp = @posts_to_display;
	@posts_to_display = ();
	foreach $elem (@tmp){
		push @posts_to_display, $elem if $elem =~ /post\.txt$/;
	}
	
	#pagination calculations
	my $pages = ceil(@posts_to_display/$posts_per_page);
	my $page = param('page') || 1;
	$page = $pages if $page > $pages;
	$page = 1 if $page <= 0;
	$page--;#change the number to be zero indexed rather than 1 indexed
	my $min = $posts_per_page*$page;
	my $max = $min;	
	if ($#posts_to_display < $posts_per_page*($page+1)-1){
		$max = $#posts_to_display;
	}
	else{
		$max = $posts_per_page*($page+1)-1;
	}
	
	my $string = "";
	my @sorted_posts = sort_posts(@posts_to_display);
	$string .=  display_posts(@sorted_posts[$min..$max]);
	
	#display pagination controls
	my $num = @posts_to_display;
	$string .= "<!-- min was $min and max was $max. Total posts is scalar $num, posts per page is $posts_per_page , number of pages is hence $pages. page is $page-->\n" if $debug;	
	$string .=  "<div class=\"pagination\">\n";
	foreach $i (1..$pages){
		if ($i == $page+1){
			$string .= "<a href=\"?page=$i\"><b>$i</b><\/a>&nbsp;\n";
			next;
		}
		$string .= "<a href=\"?page=$i\">$i<\/a>&nbsp;\n";
	}
	$string .=  "<\/div>\n";

	return $string;
}

sub post_search {
	my ($search, @posts) = @_;
	#search through posts
	my @results = ();
	foreach $post_dir (@posts){
		my $post_file = "$post_dir/post.txt";
		my $in_post=0;#boolean for storing if this post has the substring. Avoids pointless searching of comments and replies
		if (open(F, $post_file)){
			foreach $line (<F>){
				if ($line =~ /^message=/){
					if ($line =~ /$search/){
						push @results, $post_file;
						$in_post = 1;
					}
					last;
				}
			}
			close F;
		}
		else{
			print "<!-- couldn't open $post_file in post search-->\n" if $debug;
		}
		next if $in_post;
		#search through comments for this post
		my @comments = sort(glob("$post_dir/comments/*"));
		foreach $comment (@comments){
			my $comment_file = "$comment/comment.txt";
			if (open(F, $comment_file)){
				foreach $line (<F>){
					if ($line =~ /^message=/){
						if ($line =~ /$search/){
							push @results, $post_file;
							$in_post = 1;
						}
						last;
					}
				}
				close F;
			}
			else{
				print "<!-- couldn't open $comment_file in post search comments-->\n" if $debug;
			}
			last if $in_post;#stops pointless seraching of replies
			#search through replies for this comment
			my @replies = sort(glob("$comment/replies/*"));
			for $reply (@replies){
				my $reply_file = "$reply/reply.txt";
				if (open(F, $reply_file)){
					foreach $line (<F>){
						if ($line =~ /^message=/){
							if ($line =~ /$search/){
								push @results, $post_file;
								$in_post = 1;
							}
							last;
						}
					}
					close F;
				}
				else{
					print "<!-- couldn't open $reply_file in post search replies-->\n" if $debug;
				}
				last if $in_post;#stops pointless seraching of replies
			}
			last if $in_post;#stops pointless seraching of comments
		}
	}#end search posts
	return @results;
}

sub post_search_page {
	my ($search) = @_;
	print page_header();
	warningsToBrowser(1);
	print navbar();
	my @posts = sort(glob("$users_dir/*/posts/*")); #for all posts
	my @results = post_search($search, @posts);
	
	#pagination calculations
	my $string = "<br>PostSearch results for: $search<br>\n<p>\n";
	my $pages = int(@results/$posts_per_page + 0.99);
	my $page = param('page') || 1;
	$page--;#change the number to be zero indexed rather than 1 indexed
	my $min = $posts_per_page*$page;
	my $max = $min;	
	if ($#results < $posts_per_page*($page+1)-1){
		$max = $#results;
	}
	else{
		$max = $posts_per_page*($page+1)-1;
	}
	
	$string .= display_posts(sort_posts(@results[$min..$max]));
		
		
	#pagination controls
	$string .= "<!-- min was $min and max was $max. Total posts is $#results , number of pages is hence $pages. page is $page-->\n" if $debug;	
	$string .=  "<div class=\"pagination\">\n";
	foreach $i (1..$pages){
		if ($i == $page+1){
			$string .=  "<a href=\"?postsearch=$search&page=$i\"><b>$i</b><\/a>&nbsp;\n";
			next;
		}
		$string .=  "<a href=\"?postsearch=$search&page=$i\">$i<\/a>&nbsp;\n";
	}
	$string .=  "<\/div>\n";
	
	$string .= "</p>";
	return $string;
}

sub new_post_box{
	my $string = "";
	$string .= "<form method=\"POST\" align=\"center\" enctype=\"multipart/form-data\">\n";
	$string .= "<div class=\"new_post_box\">\n";
	#$string .= "<input type=\"text\" name=\"newpost\">\n";
	$string .= "<textarea name=\"newpost\"  cols=\"40\" rows=\"2\"></textarea>";
	$string .= "<label class=\"matelook_button\">Attach a picture or video<input type=\"file\" name=\"file_upload\" class=\"inputfile\" accept=\"video/mp4, image/jpeg\"></label>\n";
	$string .= "<input type=\"submit\" value=\"Post\" class=\"matelook_button\">\n";
	$string .= "</form>\n";
	$string .= "</div>";
	$string .= "<br>";
	return $string;
}

sub remove_from_list { #remove the specified element from a perl list
	my ($rm_elem, @initial_list) = @_;
	my @final_list = ();
	for my $elem (@initial_list){
		next if $elem eq $rm_elem;
		push @final_list, $elem;
	}
	return @final_list;
}

sub in_list_variable { # returns 1 if the search term is in the perl list
	my ($search, @list) = @_;
	foreach $elem (@list){
		chomp $elem;
		if ($elem eq $search){
			return 1;
		}
	}
	return 0;
}

sub in_list{
	my ($list, $zid) = @_;
	if (open(IN_LIST, '<', "$users_dir/$username/user.txt")){
		foreach $line (<IN_LIST>){
			if ($line =~ /^$list=/){
				foreach $user ($line =~ /z[0-9]{7}/g){
					if ($user eq $zid){
						return 1;
					}
				}
				return 0;
			}
		}#end foreach line
		close IN_LIST;
		print "<!-- couldn't find a list of mates-->\n" if $debug;
		return 0;
	}
	else{
		print "<!-- error in is_fiend, couldn't open details-->" if $debug;
		return 0;
	}
}

sub user_page {
	my ($parameter, $message,$colour) = @_;
	my $user_to_show = "$users_dir/$parameter";
	my $user_is_mate = 0;
	my $zid_to_show = $user_to_show;
	$zid_to_show =~ s/$users_dir\///g;
	
	my $debug_message = "";

	my $full_name = "";
	my $profile_text = "";
	my $program = "";
	my $home_suburb = "";
	my $birthday = "";
	my $courses = "";
	my @public_fields = ();
	my $mates = "";
	
	#read the details file
	my $details_filename = "$user_to_show/user.txt";
	open my $p, "$details_filename" or die "can not open $details_filename: $!";
	while ($line = <$p>){
		next if $line =~ /^email|^password|^home_latitude|^home_longitude|^mate_request_handle|^pending_mate_requests|^mate_request_email|^mention_email/;
		$line =~ s/=/: /;
		if ($line =~ /^mates/){
			$line =~ s/\[|\]//g;#remove braces
			$mates = replace_zid($line);
			$line =~ s/^mates: //;
			my @mates = split(',', $line);
			$user_is_mate = in_list_variable($username,@mates);
			$debug_message .= "user_is_mate is $user_is_mate, searched for $username in @mates\n" if $debug;
		}
		elsif ($line =~ /^profile_text/){
			#$profile_text = convert_newline(replace_links(profile_text_tags($line)));
			#$profile_text = replace_links(profile_text_tags($line));
			$profile_text = undo_saved_newline(replace_links(profile_text_tags($line)));
		}
		elsif ($line =~ /^program/){
			$program = $line;
		}
		elsif ($line =~ /^home_suburb/){
			$home_suburb = $line;
		}
		elsif ($line =~ /^birthday/){
			$birthday = $line;
		}
		elsif ($line =~ /^courses/){
			$courses = $line;
		}
		elsif ($line =~ /^full_name/){
			$full_name = $line;
		}
		elsif ($line =~ /^public_fields/){
			$line =~ s/public_fields: //g;
			@public_fields = split(',', $line);
		}
	}
	close $p;
	
	#true when the user is viewing their own profile or a friends
	my $friend_or_i = ($zid_to_show eq $username) || $user_is_mate;
	
	#see if there is a background image
	my $background_image = "$user_to_show/background.jpg";
	if (open(my $pic, "$background_image") && ($friend_or_i || in_list_variable("back_img",@public_fields))){
		print page_header($background_image);
	}
	else{
		print page_header();
	}
	warningsToBrowser(1);
	print "<!-- public fields is @public_fields-->\n" if $debug;
	print "<!-- debug message in user page is $debug_message-->\n" if $debug;
	
	print navbar();
	#print error or success message
	if ($message){
		print "\n<br>\n<span style=\"color: $colour\">$message</span><br>";
	}
	
	if ($friend_or_i || in_list_variable("prof_img",@public_fields)){
		my $image_file = "$user_to_show/profile.jpg"; # all dataset pictures are .jpg
		if (open my $pic, "$image_file"){
			print "<img src=\"$image_file\" style=\"width:304px;height:228px;\">\n";
		}
		else{
			print "<!-- failed to open $image_file -->\n" if $debug;
		}
	}
	
	#populate details
	my $details = "";
	$details .= $full_name;
	$details .= $mates if $friend_or_i || in_list_variable("mates",@public_fields);
	$details .= $program if $friend_or_i || in_list_variable("program",@public_fields);
	$details .= $profile_text if $friend_or_i || in_list_variable("profile_text",@public_fields);
	$details .= $home_suburb if $friend_or_i || in_list_variable("home_suburb",@public_fields);
	$details .= $birthday if $friend_or_i || in_list_variable("birthday",@public_fields);
	$details .= $courses if $friend_or_i || in_list_variable("courses",@public_fields);
	
	if ($username eq $zid_to_show){#print an edit button at the end of the user's details
		$details .= "<form method=\"GET\" align=\"right\">";
		$details .= "<input type=\"submit\" value=\"Edit\" name=\"edit\" class=\"matelook_button\">";
		$details .= "</form>";
	}
	elsif (in_list("mate_request_handle", $zid_to_show)){#accept/decline button
		$details .= "<form method=\"POST\" align=\"right\">";
		$details .= "<input type=\"submit\" value=\"Accept\" name=\"accept_decline\" class=\"matelook_button\">";
		$details .= "<input type=\"submit\" value=\"Decline\" name=\"accept_decline\" class=\"matelook_button\">";
		$details .= "<input type=\"hidden\" value=\"$zid_to_show\" name=\"zid_to_mate\">";
		$details .= "</form>";
	}
	elsif (in_list("mates", $zid_to_show)){#show unmate button
		$details .= "<form method=\"POST\" align=\"right\">";
		$details .= "<input type=\"submit\" value=\"Unmate\" name=\"unmate_user\" class=\"matelook_button\">";
		$details .= "<input type=\"hidden\" value=\"$zid_to_show\" name=\"zid_to_unmate\">";
		$details .= "</form>";
	}
	elsif (in_list("pending_mate_requests", $zid_to_show)){#mate request pending
		$details .= "<div align=\"right\">";
		$details .= "<input type=\"submit\" value=\"Mate request pending\" class=\"matelook_button\" disabled>\n";
		$details .= "</div>";
	}
	else{#show mate button
		$details .= "<form method=\"POST\" align=\"right\">";
		$details .= "<input type=\"submit\" value=\"Mate\" name=\"mate_user\" class=\"matelook_button\">";
		$details .= "<input type=\"hidden\" value=\"$zid_to_show\" name=\"zid_to_mate\">";
		$details .= "</form>";
	}

	#display user posts
	my $posts = "";
	if ($friend_or_i || in_list_variable("posts",@public_fields)){
		my @posts = glob "$user_to_show/posts/*/post.txt";
		#my @sorted = reverse sort {$a =~ m/\/\d+\// <=> $b =~ m/\/\d+\//} @posts;
		$posts = "Posts: <br>";
		
		#remove things that aren't post.txt
		my @tmp = @posts;
		@posts = ();
		foreach $elem (@tmp){
			push @posts, $elem if $elem =~ /post\.txt$/;
		}
		
		#$posts .= display_posts(@sorted);
		my $pages = int(@posts/$posts_per_page + 0.99);
		my $page = param('page') || 1;
		$page = $pages if $page > $pages;
		$page = 1 if $page <= 0;
		$page--;#change the number to be zero indexed rather than 1 indexed
		my $min = $posts_per_page*$page;
		my $max = $min;	
		if ($#posts < $posts_per_page*($page+1)-1){
			$max = $#posts;
		}
		else{
			$max = $posts_per_page*($page+1)-1;
		}
		my @sorted_posts = sort_posts(@posts);
		$posts .= display_posts(@sorted_posts[$min..$max]);
		
		$posts .= "<!-- min was $min and max was $max. Total posts is $#posts+1 , number of pages is hence $pages. page is $page-->\n";	
		$posts .=  "<div class=\"pagination\">\n";
		foreach $i (1..$pages){
			if ($i == $page+1){
				$posts .=  "<a href=\"?user_page=$zid_to_show&page=$i\"><b>$i</b><\/a>&nbsp;\n";
				next;
			}
			$posts .=  "<a href=\"?user_page=$zid_to_show&page=$i\">$i<\/a>&nbsp;\n";
		}
		$posts .=  "<\/div>\n";
	}
	else{
		$posts = "This user has not chosen to make their posts public";
	}

	return <<eof
<div class="matelook_user_details">
$details
</div>
$posts
<p>
eof
}

sub edit_details_page {
	print page_header();
	warningsToBrowser(1);

	print navbar();
	my $full_name = "";
	my $program = "";
	my $profile_text = "";
	my $home_suburb = "";
	my $birthday = "";
	my $courses = "";
	my $password_update = "";
	my $image = "";
	my $mate_request_email = "";
	my $mention_email = "";
	my @public_fields = ();

	#get current values
	open my $p, "$details_filename" or die "can not open $details_filename: $!";
	while ($line = <$p>){
		chomp $line;
		if ($line =~ /^full_name=/){
			$line =~ s/^full_name=//g;
			$full_name = $line;
		}
		elsif ($line =~ /^program=/){
			$line =~ s/^program=//g;
			$program = $line;
		}
		elsif ($line =~ /^profile_text=/){
			$line =~ s/^profile_text=//g;
			$profile_text = $line;
		}
		elsif ($line =~ /^home_suburb=/){
			$line =~ s/^home_suburb=//g;
			$home_suburb = $line;
		}
		elsif ($line =~ /^courses=/){
			$line =~ s/^courses=//g;
			$courses = $line;
		}
		elsif ($line =~ /^password=/){
			$line =~ s/^password=//g;
			$password_update = $line;
		}
		elsif ($line =~ /^birthday=/){
			$line =~ s/^birthday=//g;
			$birthday = $line;
		}
		elsif ($line =~ /^mate_request_email=/){
			$line =~ s/^mate_request_email=//g;
			$mate_request_email = $line;
		}
		elsif ($line =~ /^mention_email=/){
			$line =~ s/^mention_email=//g;
			$mention_email = $line;
		}
		elsif ($line =~ /^public_fields=/){
			$line =~ s/^public_fields=//g;
			@public_fields = split(',',$line);
			print "<!-- public fields is @public_fields-->" if $debug;
		}
	}
	close $p;

	my $string = "<form method=\"POST\" enctype=\"multipart/form-data\">\n";
	$string .= "Full name: <input type=\"text\" name=\"full_name\" value=\"$full_name\"><br>\n";
	#program
	$string .= "Program: <input type=\"text\" name=\"program\" value=\"$program\">\n";
	if (in_list_variable("program", @public_fields)){
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_program\" value=\"program\" checked><br>\n";
	}
	else{
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_program\" value=\"program\"><br>\n";
	}
	#profile text
	my $text_to_display = undo_saved_newline($profile_text);
	$string .= "Profile text: <textarea name=\"profile_text\" value=\"$profile_text\" cols=\"40\" rows=\"5\">$text_to_display</textarea>\n";
	if (in_list_variable("profile_text", @public_fields)){
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_profile_text\" value=\"profile_text\" checked><br>\n";
	}
	else{
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_profile_text\" value=\"profile_text\"><br>\n";
	}
	#home suburb
	$string .= "Home suburb: <input type=\"text\" name=\"home_suburb\" value=\"$home_suburb\">\n";
	if (in_list_variable("home_suburb", @public_fields)){
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_home_suburb\" value=\"home_suburb\" checked><br>\n";
	}
	else{
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_home_suburb\" value=\"home_suburb\"><br>\n";
	}
	#birthday
	$string .= "Birthday: <input type=\"date\" name=\"date\" value=\"$birthday\">\n";
	if (in_list_variable("birthday", @public_fields)){
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_birthday\" value=\"birthday\" checked><br>\n";
	}
	else{
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_birthday\" value=\"birthday\"><br>\n";
	}
	#courses
	$string .= "Courses: <input type=\"text\" name=\"courses\" value=\"$courses\" class=\"wide_text_box\">\n";
	if (in_list_variable("courses", @public_fields)){
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_courses\" value=\"courses\" checked><br>\n";
	}
	else{
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_courses\" value=\"courses\"><br>\n";
	}
	#password, but only if in debug mode
	$string .= "Password: <input type=\"text\" name=\"password_update\" value=\"$password_update\"><br>\n" if $debug;
	#profile image
	$string .= "Profile Image (must be .jpg): <label class=\"matelook_button\">Choose a profile picture<input type=\"file\" name=\"img_file\" accept=\"image/*\"></label>";
	$string .= "<input type=\"submit\" value=\"Delete\" name=\"del_prof_img\" class=\"matelook_button\">\n";
	if (in_list_variable("prof_img", @public_fields)){
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_prof_img\" value=\"prof_img\" checked><br>\n";
	}
	else{
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_prof_img\" value=\"prof_img\"><br>\n";
	}
	#background image 
	$string .= "Background Image (must be .jpg): <label class=\"matelook_button\">Choose a profile picture<input class=\"fileInput\" type=\"file\" name=\"file1\"/></label>";
	$string .= "<input type=\"submit\" value=\"Delete current profile picture\" name=\"del_back_img\" class=\"matelook_button\">\n";
	if (in_list_variable("back_img", @public_fields)){
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_back_img\" value=\"back_img\" checked><br>\n";
	}
	else{
		$string .= "Visible to public?: <input type=\"checkbox\" name=\"public_prof_img\" value=\"back_img\"><br>\n";
	}
	#mate visibility
	if (in_list_variable("mates", @public_fields)){
		$string .= "Mates visible to public?: <input type=\"checkbox\" name=\"public_mates\" value=\"mates\" checked><br>\n";
	}
	else{
		$string .= "Mates visible to public?: <input type=\"checkbox\" name=\"public_mates\" value=\"mates\"><br>\n";
	}
	#post visibility
	if (in_list_variable("posts", @public_fields)){
		$string .= "Posts visible to public?: <input type=\"checkbox\" name=\"public_posts\" value=\"posts\" checked><br>\n";
	}
	else{
		$string .= "Posts visible to public?: <input type=\"checkbox\" name=\"public_posts\" value=\"posts\"><br>\n";
	}
	#ask if they want  tp recieve notifications for mate requests and mentions
	if ($mate_request_email ne "true"){
		$string .= "Recieve email notifications for mate request: <input type=\"checkbox\" name=\"mate_request_email\" value=\"true\"><br>\n";
	}
	else{
		$string .= "Recieve email notifications for mate request: <input type=\"checkbox\" name=\"mate_request_email\" value=\"true\" checked><br>\n";
	}
	if ($mention_email ne "true"){
		$string .= "Recieve email notifications when mentioned in a post, comment or reply: <input type=\"checkbox\" value=\"true\" name=\"mention_email\"><br>\n";
	}
	else{
		$string .= "Recieve email notifications when mentioned in a post, comment or reply: <input type=\"checkbox\" value=\"true\" name=\"mention_email\" checked><br>\n";
	}
	$string .= "<input type=\"submit\" value=\"Save\" name=\"save\" class=\"matelook_button\"><br>\n";
	$string .= "</form>\n";
	return $string;
}

sub login_page {
	my ($message,$colour) = @_;
	chomp $message;
	my $string = "";
	$string .= start_form;
	if ($message){
		$string .= "\n<br>\n<span style=\"color: $colour\">$message</span><br>";#error/success messages
	}
	$string .= "Username:\n".textfield('username')."\n";
	$string .= "Password:\n".password_field('password')."\n";
	$string .= "<input type=\"submit\" name=\"value\" value=\"Login\" class=\"matelook_button\"/>\n";
	$string .= end_form."\n";
	$string .= "<a href=\"?forgot_password=true\">Help, I forgot my password!</a>\n";

	#create new account
	$string .= "<br><p>";
	$string .= "Or Create a new account";
	$string .= "<form method=\"POST\">\n";
	$string .= "Zid: <input type=\"text\" name=\"zid\"><br>\n";
	$string .= "Password: <input type=\"password\" name=\"newpassword\"><br>\n";
	$string .= "Confirm Password: <input type=\"password\" name=\"confirmpassword\"><br>\n";
	$string .= "Email: <input type=\"email\" name=\"email\"><br>\n";
	$string .= "<input type=\"submit\" value=\"Create Account\" name=\"newaccount\" class=\"matelook_button\"><br>\n";
	$string .= "</form>\n";
	$string .= "</p>";

	return $string;
}

# HTML placed at the top of every page
#javascript function is from http://stackoverflow.com/questions/10537080/html-button-that-clears-cookies-and-redirects-to-an-html-page
sub page_header {
	my ($background) = @_;
	if (!$background){
		$background = "";
	}
	my $string = header(-charset => "utf-8");
    return <<eof;
$string

<!DOCTYPE html>
<html lang="en">
<head>
<script>
function deleteAllCookies() {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];
        var eqPos = cookie.indexOf("=");

        var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
}

function clearAndRedirect(link) {
    deleteAllCookies();
    document.location = link;
}
</script>
<title>matelook</title>
<link href="matelook.css" rel="stylesheet">
</head>
<body background="$background">
<div class="matelook_heading">
matelook
</div>
eof
}

sub hidden_login {
	my $string = "";
	$string .= hidden(-name=>"username")."\n";
	$string .= hidden(-name=>"password")."\n";
	return $string;
}

sub get_matelist {
	my $string = "";
	#get list of mates
	my @mate_list = ();
	$details_filename = "$users_dir/$username/user.txt";
	open my $p, "$details_filename" or die "can not open $details_filename: $!";
	while (my $line = <$p>){
		chomp $line;
		if ($line =~ /^mates=\[(.*)\]/){
			@mate_list = split(',',$1);
			last;
		}
	}
	close $p;
	#foreach mate
	if (@mate_list == 0){
		print "<!-- matelist for $username is empty-->" if $debug;
	}
	foreach $mate (@mate_list){
		$mate =~ s/(^ *)|( *$)//g;#remove leading and trailing whitespace
		$string .= get_pic($mate);#print profile pic
		$string .= "<a href=?user_page=$mate>\n";
		$string .= replace_zid($mate);#print mate name
		$string .= "\n</a>\n";
	}
	return $string;
}

sub navbar {
	my $string = "";
	my $matelist = get_matelist();

	#$string .=  "<ul class=\"navbar\">\n";
	$string .=  "<ul>\n";
	$string .=  "<li><a href=\"${\this_url()}\">Home  </a></li>";#home button
	$string .=  "<li>Logged in as: <a href=?user_page=$username>${\replace_zid($username)}</a></li>";
	$string .=  "<li><form method=\"GET\" align=\"center\">Find mates<input type=\"search\" name=\"matesearch\"><input type=\"submit\" value=\"Search mates\" class=\"matelook_button\"></form></li>";
	$string .=  "<li><form method=\"GET\" align=\"center\">Find posts<input type=\"search\" name=\"postsearch\"><input type=\"submit\" value=\"Search posts\" class=\"matelook_button\"></form></li>";
	$string .=  "<li style=\"float:right\"><a href=\"javascript:clearAndRedirect('${\this_url()}')\"><input type=\"submit\" class=\"matelook_button\" value=\"Logout\" align=\"right\"></a></li>";
	$string .=  "</ul>\n";
	$string .=  "<br>\n";
	$string .=  "<div class=\"matelist\">";
	$string .=  "$matelist\n";
	$string .=  "</div>";
	$string .=  "<br>";
	return $string;
}

# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
sub page_trailer {
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

main();
