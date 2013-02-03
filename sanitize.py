import unicodedata

def sanitize_path_fragment(
		original_fragment,
		target_file_systems = {'btrfs', 'ext', 'ext2', 'ext3', 'ext3cow', 'ext4', 'exfat', 'fat32', 'hfs+', 'ntfs_win32', 'reiser4', 'reiserfs', 'xfs', 'zfs'},
		sanitization_method = 'underscore',
		truncate = True
	):
	sanitized_fragment = unicodedata.normalize('NFC', original_fragment)
	if sanitization_method == 'underscore':
		illegal_characters = {
			'btrfs': {'\0', '/'},
			'ext': {'\0', '/'},
			'ext2': {'\0', '/'},
			'ext3': {'\0', '/'},
			'ext3cow': {'\0', '/', '@'},
			'ext4': {'\0', '/'},
			'exfat': {
				'\00', '\01', '\02', '\03', '\04', '\05', '\06', '\07', '\10', '\11', '\12', '\13', '\14', '\15', '\16', '\17',
				'\20', '\21', '\22', '\23', '\24', '\25', '\26', '\27', '\30', '\31', '\32', '\33', '\34', '\35', '\36', '\37',
				'/', '\\', ':', '*', '?', '<', '>', '|',
			},
			'fat32': { # TODO: Confirm this list; current list is just a wild guess, assuming UTF-16 encoding.
				'\00', '\01', '\02', '\03', '\04', '\05', '\06', '\07', '\10', '\11', '\12', '\13', '\14', '\15', '\16', '\17',
				'\20', '\21', '\22', '\23', '\24', '\25', '\26', '\27', '\30', '\31', '\32', '\33', '\34', '\35', '\36', '\37',
				'/', '\\', ':', '*', '?', '<', '>', '|',
			},
			'hfs+': {'\0', '/', ':'}, # In theory, all Unicode characters, including NUL, are usable (HFS+ is awesome in this way); so this is just a sane set for legacy compatibility
			'ntfs_win32': {'\0', '/', '\\', ':', '*', '?', '"', '<', '>', '|'}, # NTFS Win32 namespace (which is stricter)
			'ntfs_posix': {'\0', '/'}, # NTFS POSIX namespace (which allows more characters)
			'reiser4': {'\0', '/'},
			'reiserfs': {'\0', '/'},
			'xfs': {'\0', '/'},
			'zfs': {'\0', '/'},
		}
		# Replace illegal characters with an underscore
		for file_system in target_file_systems:
			for character in illegal_characters[file_system]:
				sanitized_fragment = sanitized_fragment.replace(character, '_')

		# Truncate if the resulting string is too long
		if truncate:
			max_lengths = {
				# 'utf-8' is only an assumption that applies to most modern Linux distros with an almost vanilla kernel with default build parameters.
				# Similarly, the kernel can be tweaked to only support filenames that are even shorter, but we don't care here.
				# The same applies to all file systems commonly found with Linux.
				# Seriously, this is 2013. The fact that the Linux community does not move to a file system with an enforced Unicode filename encoding is as bad as Microsoft with Windows 95, some 18 years ago.
				# If you add more file systems, see if it is affected by Unicode Normal Forms, like HFS+; You may have to take extra care in editing the actual sanitization routine below.
				'btrfs': (255, 'bytes', 'utf-8', 'NFC'),
				'ext': (255, 'bytes', 'utf-8', 'NFC'),
				'ext2': (255, 'bytes', 'utf-8', 'NFC'),
				'ext3': (255, 'bytes', 'utf-8', 'NFC'),
				'ext3cow': (255, 'bytes', 'utf-8', 'NFC'),
				'ext4': (255, 'bytes', 'utf-8', 'NFC'),
				'exfat': (255, 'characters', 'utf-16', 'NFC'),
				'fat32': (255, 'characters', 'utf-16', 'NFC'), # 'utf-16' is not entirely true. FAT32 used to be used with codepages; but since Windows XP, the default seems to be UTF-16.
				'hfs+': (255, 'characters', 'utf-16', 'NFD'), # FIXME: improve HFS+ handling, because it does not use the standard NFD. It's close, but it's not exactly the same thing.
				'ntfs_win32': (255, 'characters', 'utf-16', 'NFC'),
				'ntfs_posix': (255, 'characters', 'utf-16', 'NFC'),
				'reiser4': (3976, 'bytes', 'utf-8', 'NFC'), # I don't care if Linux can't support >255 bytes. The adoption of filenames longer than 255 bytes is long overdue.
				'reiserfs': (4032, 'bytes', 'utf-8', 'NFC'), # Same here.
				'xfs': (255, 'bytes', 'utf-8', 'NFC'),
				'zfs': (255, 'bytes', 'utf-8', 'NFC'),
			}
			for file_system in target_file_systems:
				if max_lengths[file_system][1] == 'bytes':
					temp_fragment_bytes = bytearray()
					for character in sanitized_fragment:
						bytes = unicodedata.normalize(max_lengths[file_system][3], character).encode(max_lengths[file_system][2])
						if len(temp_fragment_bytes + bytes) <= max_lengths[file_system][0]:
							temp_fragment_bytes.extend(bytes)
						else:
							break
					sanitized_fragment = temp_fragment_bytes.decode(max_lengths[file_system][2])
				else: # Assume 'characters'
					temp_fragment = unicodedata.normalize(max_lengths[file_system][3], sanitized_fragment)
					sanitized_fragment = temp_fragment[:min(len(temp_fragment), max_lengths[file_system][0])]
	else:
		raise ValueError("sanitization_method must be a valid sanitization method")
	return sanitized_fragment
